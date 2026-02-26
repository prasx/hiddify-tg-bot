"""
Сервис для уведомлений и рассылок.
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import List, Tuple

from aiogram import Bot

import database as db
import config
from services.hiddify_service import HiddifyService
from keyboards.subscription import subscription_action_buttons


logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений и рассылок."""
    
    def __init__(self, bot: Bot, hiddify_service: HiddifyService):
        """
        Инициализация сервиса уведомлений.
        
        Args:
            bot: Экземпляр бота
            hiddify_service: Сервис для работы с Hiddify API
        """
        self.bot = bot
        self.hiddify = hiddify_service
        logger.info("NotificationService инициализирован")
    
    async def broadcast_message(
        self,
        admin_id: int,
        message_text: str,
        users: List[int]
    ) -> Tuple[int, int, List[Tuple[int, str]]]:
        """
        Отправить сообщение всем пользователям.
        
        Args:
            admin_id: ID администратора для отчёта
            message_text: Текст сообщения
            users: Список ID пользователей
            
        Returns:
            Кортеж (успешно, неудачи, список ошибок)
        """
        successful_deliveries = []
        failed_deliveries = []

        for user_id in users:
            try:
                await self.bot.send_message(user_id, message_text, parse_mode="HTML")
                successful_deliveries.append(user_id)
            except Exception as e:
                failed_deliveries.append((user_id, str(e)))
                logger.warning(f"Не удалось доставить сообщение пользователю {user_id}: {e}")

        # Отправляем отчёт админу
        summary_message = (
            f"‼️ Рассылка завершена.\n\n"
            f"✅ Успешно доставлено: {len(successful_deliveries)} пользователям.\n"
            f"❌ Не удалось доставить: {len(failed_deliveries)} пользователям.\n"
        )

        if failed_deliveries:
            summary_message += "\n<b>😱 Список пользователей, которым не удалось доставить сообщение:</b>\n"
            for user_id, error in failed_deliveries[:20]:  # Ограничиваем вывод
                summary_message += f"ID: {user_id}, Ошибка: {error}\n"
            if len(failed_deliveries) > 20:
                summary_message += f"... и ещё {len(failed_deliveries) - 20} пользователей"

        await self.bot.send_message(admin_id, summary_message, parse_mode="HTML")
        
        return len(successful_deliveries), len(failed_deliveries), failed_deliveries
    
    async def notify_payment_received(self, user_id: int, target_user_id: int) -> None:
        """
        Уведомить админа о получении подтверждения платежа.
        
        Args:
            user_id: ID пользователя, отправившего подтверждение
            target_user_id: ID получателя платежа (админ)
        """
        user = db.get_user(user_id)
        username = "Unknown"
        if user and user[3]:
            try:
                profile = json.loads(user[3])
                username = profile.get("username", "Unknown")
            except json.JSONDecodeError:
                pass
        
        admin_id = config.BotConfig.ADMIN_PAYMENTS
        message_text = f"Пользователь @{username} (ID: {target_user_id}) подтвердил пополнение баланса."
        
        await self.bot.send_message(admin_id, message_text)
        logger.info(f"Админ уведомлён о подтверждении платежа от пользователя {user_id}")
    
    async def send_expiring_notification(
        self,
        user_id: int,
        days_left: int,
        balance: float,
        charge_amount: float | None
    ) -> None:
        """
        Отправить уведомление об истечении подписки.
        
        Args:
            user_id: ID пользователя
            days_left: Осталось дней до истечения
            balance: Баланс пользователя
            charge_amount: Стоимость продления
        """
        keyboard = subscription_action_buttons(balance, charge_amount)
        
        if days_left == 1:
            warning = "❗️ Срок вашей подписки истекает через 1 день! Продлите услугу во избежание отключения."
        elif days_left == 4:
            warning = "⚠️ Ваша подписка истекает через 4 дня! Пожалуйста, продлите действие, чтобы не потерять доступ."
        else:
            return
        
        try:
            await self.bot.send_message(user_id, warning, reply_markup=keyboard.as_markup())
            logger.info(f"Уведомление об истечении подписки отправлено пользователю {user_id} ({days_left} дней)")
        except Exception as e:
            logger.warning(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
    
    async def check_and_notify_expiring_users(self) -> None:
        """
        Проверить всех пользователей и отправить уведомления об истечении подписки.
        Запускается по расписанию (ежедневно в 16:20).
        """
        users = db.get_all_user_ids()
        logger.info(f"Проверка {len(users)} пользователей на истечение подписки")
        
        for user_id in users:
            user = db.get_user(user_id)
            
            # Пропускаем пользователей без UUID
            if not user or not user[2] or user[2] == "N/A":
                continue
            
            uuid = user[2]
            
            try:
                user_info = self.hiddify.get_user_info(uuid)
            except Exception as e:
                logger.warning(f"Ошибка при получении user_info для {uuid}: {e}")
                continue
            
            start_date_str = user_info.get("start_date")
            package_days = user_info.get("package_days")
            
            if not start_date_str or not package_days or str(start_date_str).lower() == "неизвестно":
                continue
            
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                expire_date = start_date + timedelta(days=int(package_days))
                days_left = (expire_date - datetime.now().date()).days
            except Exception:
                continue
            
            # Отправляем уведомления за 1 и 4 дня до истечения
            if days_left in (1, 4):
                try:
                    profile_data = None
                    if user and user[3]:
                        try:
                            profile_data = json.loads(user[3])
                        except Exception:
                            pass
                    
                    balance = profile_data.get("balance", 0) if profile_data else 0
                    ticket_tariff = profile_data.get("ticket_tariff", {}) if profile_data else {}
                    charge_amount = ticket_tariff.get("price")
                    
                    await self.send_expiring_notification(user_id, days_left, balance, charge_amount)
                except Exception as e:
                    logger.warning(f"Ошибка при отправке уведомления пользователю {user_id}: {e}\n{traceback.format_exc()}")
    
    async def start_scheduled_notifications(self) -> None:
        """
        Запустить фоновую задачу уведомлений об истечении подписки.
        Уведомления отправляются ежедневно в 16:20.
        """
        while True:
            now = datetime.now()
            next_run = now.replace(hour=16, minute=20, second=0, microsecond=0)
            
            if now >= next_run:
                next_run += timedelta(days=1)
            
            sleep_seconds = (next_run - now).total_seconds()
            logger.info(f"Следующая проверка уведомлений через {sleep_seconds:.0f} секунд")
            
            await asyncio.sleep(sleep_seconds)
            await self.check_and_notify_expiring_users()
