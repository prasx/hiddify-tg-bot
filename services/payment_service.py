"""
Сервис для обработки платежей.
"""

import json
import logging
from typing import Optional

from aiogram import Bot

import database as db
import config
from keyboards.payment import admin_payment_buttons


logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для управления платежами и балансом."""
    
    def __init__(self, bot: Bot):
        """
        Инициализация сервиса платежей.
        
        Args:
            bot: Экземпляр бота для отправки уведомлений
        """
        self.bot = bot
        logger.info("PaymentService инициализирован")
    
    def add_balance(self, user_id: int) -> float:
        """
        Добавить баланс пользователю (на фиксированную сумму 400 руб).
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Новый баланс пользователя
        """
        db.add_balance(user_id)
        new_balance = db.get_user_balance(user_id)
        logger.info(f"Баланс пользователя {user_id} пополнен на 400 руб. Новый баланс: {new_balance}")
        return new_balance
    
    def update_balance(self, user_id: int, amount: float) -> float:
        """
        Обновить баланс пользователя на указанную сумму.
        
        Args:
            user_id: Telegram ID пользователя
            amount: Сумма пополнения
            
        Returns:
            Новый баланс пользователя
        """
        db.update_balance(user_id, amount)
        new_balance = db.get_user_balance(user_id)
        logger.info(f"Баланс пользователя {user_id} обновлён на {amount} руб. Новый баланс: {new_balance}")
        return new_balance
    
    def get_balance(self, user_id: int) -> float:
        """
        Получить баланс пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Текущий баланс
        """
        return db.get_user_balance(user_id)
    
    async def notify_admin_about_payment(self, user_id: int, amount: float) -> None:
        """
        Уведомить админа о создании запроса на оплату.
        
        Args:
            user_id: Telegram ID пользователя
            amount: Сумма оплаты
        """
        user = db.get_user(user_id)
        username = "Unknown"
        if user and user[3]:
            try:
                profile = json.loads(user[3])
                username = profile.get("username", "Unknown")
            except json.JSONDecodeError:
                pass
        
        keyboard = admin_payment_buttons(user_id)
        
        admin_id = config.BotConfig.ADMIN_PAYMENTS
        message_text = (
            f"⚠️ <b>@{username}</b> <i>(ID: {user_id})</i> создал запрос.\n\n"
            f"Сумма: <b>{amount} рублей.</b>\n"
            f"❗️Не пополняйте баланс пока пользователь не пришлёт скриншот и сообщение с подтверждение оплаты!"
        )
        
        await self.bot.send_message(
            admin_id,
            message_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
        logger.info(f"Админ уведомлён о платеже пользователя {user_id} на сумму {amount}")
    
    async def notify_user_payment_confirmed(self, user_id: int, duration: str) -> None:
        """
        Уведомить пользователя о подтверждении платежа.
        
        Args:
            user_id: Telegram ID пользователя
            duration: Длительность активированной подписки
        """
        message_text = f"✅ Ваш платеж подтвержден! Подписка на {duration} активирована."
        await self.bot.send_message(user_id, message_text, parse_mode="HTML")
        logger.info(f"Платёж пользователя {user_id} подтверждён, подписка на {duration} активирована")
    
    async def notify_admin_payment_confirmed(self, user_id: int, amount: float) -> None:
        """
        Уведомить админа о подтверждении платежа.
        
        Args:
            user_id: Telegram ID пользователя
            amount: Сумма платежа
        """
        admin_id = config.BotConfig.ADMIN_PAYMENTS
        message_text = f"💰 Баланс пользователя {user_id} пополнен на {amount} рублей."
        await self.bot.send_message(admin_id, message_text)
        logger.info(f"Админ уведомлён о подтверждении платежа пользователя {user_id}")
    
    def calculate_service_cost(self, package_days: int) -> int:
        """
        Рассчитать стоимость услуги.
        
        Args:
            package_days: Количество дней подписки
            
        Returns:
            Стоимость в рублях
        """
        return 400 * (package_days // 30)
    
    def check_sufficient_balance(self, user_id: int, required_amount: float) -> bool:
        """
        Проверить достаточность баланса.
        
        Args:
            user_id: Telegram ID пользователя
            required_amount: Требуемая сумма
            
        Returns:
            True если баланс достаточен
        """
        balance = self.get_balance(user_id)
        return balance >= required_amount
