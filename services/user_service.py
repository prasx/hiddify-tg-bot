"""
Сервис для работы с пользователями.
"""

import json
import logging
from typing import Optional, Dict, Any

import database as db


logger = logging.getLogger(__name__)


class UserService:
    """Сервис для управления пользователями."""
    
    @staticmethod
    def get_user(user_id: int) -> Optional[tuple]:
        """
        Получить информацию о пользователе из БД.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Кортеж с данными пользователя или None
        """
        return db.get_user(user_id)
    
    @staticmethod
    def get_user_balance(user_id: int) -> float:
        """
        Получить баланс пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Баланс пользователя
        """
        return db.get_user_balance(user_id)
    
    @staticmethod
    def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить профиль пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            dict с профилем или None
        """
        user = db.get_user(user_id)
        if not user or not user[3]:
            return None
        
        try:
            return json.loads(user[3])
        except json.JSONDecodeError:
            logger.error(f"Ошибка парсинга профиля пользователя {user_id}")
            return None
    
    @staticmethod
    def add_user(user_id: int, username: str, balance: float = 0.0) -> None:
        """
        Добавить нового пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            username: Имя пользователя в Telegram
            balance: Начальный баланс
        """
        db.add_user(user_id, username, balance)
        logger.info(f"Пользователь {username} (ID: {user_id}) зарегистрирован")
    
    @staticmethod
    def update_user_uuid(user_id: int, uuid: str) -> None:
        """
        Обновить UUID пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            uuid: Новый UUID от Hiddify
        """
        db.update_user_uuid(user_id, uuid)
        logger.info(f"UUID обновлён для пользователя {user_id}: {uuid}")
    
    @staticmethod
    def update_user_profile(user_id: int, profile_data: dict) -> None:
        """
        Обновить профиль пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            profile_data: Новые данные профиля
        """
        db.update_user_profile(user_id, json.dumps(profile_data))
        logger.info(f"Профиль обновлён для пользователя {user_id}")
    
    @staticmethod
    def update_user_tariff(user_id: int, tariff: dict) -> None:
        """
        Обновить тариф пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            tariff: Данные тарифа
        """
        db.update_user_tariff(user_id, tariff)
        logger.info(f"Тариф обновлён для пользователя {user_id}")
    
    @staticmethod
    def get_user_info_text(user_id: int, hiddify_service=None) -> str:
        """
        Получить текстовое представление информации о пользователе.
        
        Args:
            user_id: Telegram ID пользователя
            hiddify_service: Сервис Hiddify для получения данных
            
        Returns:
            Строка с информацией о пользователе
        """
        user_info = db.get_user(user_id)
        
        if not user_info:
            return "Привет! Я бот для работы с Hiddify API. Выберите действие:"
        
        profile_data = json.loads(user_info[3]) if user_info[3] else {}
        username = profile_data.get("username", "Неизвестно")
        balance = profile_data.get("balance", 0.0)
        
        uuid = user_info[2]
        if not uuid or uuid == "N/A":
            return (
                "⚠️ <b>У вас нет активной подписки.</b>\n\n"
                "Чтобы начать пользоваться сервисом, выберите тариф."
            )
        
        # Если есть сервис Hiddify, получаем данные от API
        if hiddify_service:
            try:
                hiddify_info = hiddify_service.get_user_info(uuid)
                
                if 'error' in hiddify_info:
                    return (
                        f"⚠️ <b>Ошибка при получении данных</b>\n\n"
                        f"👤 <b>Никнейм:</b> {username}\n"
                        f"💵 <b>Баланс:</b> {balance} руб.\n"
                        f"🆔 <b>User ID:</b> {user_id}\n\n"
                        f"❌ {hiddify_info['error']}\n\n"
                        f"Попробуйте позже или обратитесь в поддержку."
                    )
                
                return (
                    f"🌐 <b>Информация о подключении</b>\n\n"
                    f"<b>🔑 Основная информация</b>\n"
                    f"👤 <b>Никнейм:</b> {username}\n"
                    f"💵 <b>Баланс:</b> {balance} руб.\n"
                    f"🆔 <b>User ID:</b> {user_id}\n\n"
                    f"<b>📊 Статус подключения</b>\n"
                    f"🟢 <b>Статус:</b> {hiddify_info.get('status', 'Неизвестно')}\n"
                    f"📅 <b>Дата активации:</b> {hiddify_info.get('start_date', 'Неизвестно')}\n"
                    f"📆 <b>Дата окончания:</b> {hiddify_info.get('expire_date', 'Неизвестно')}\n"
                    f"📊 <b>Использовано трафика:</b> {hiddify_info.get('current_usage_gb', 0):.2f} GB / {hiddify_info.get('usage_limit_gb', 'N/A')} GB\n"
                    f"📡 <b>Последний онлайн:</b> {hiddify_info.get('last_online', 'Неизвестно')}\n\n"
                    f"<b>⚠️ ВАЖНО: </b> Не передавайте свои ключи и ссылки третьим лицам."
                )
                
            except Exception as e:
                logger.error(f"Ошибка при получении информации о пользователе: {e}")
                return (
                    f"⚠️ <b>Ошибка подключения</b>\n\n"
                    f"👤 <b>Никнейм:</b> {username}\n"
                    f"💵 <b>Баланс:</b> {balance} руб.\n"
                    f"🆔 <b>User ID:</b> {user_id}\n\n"
                    f"Не удалось получить данные с сервера. Попробуйте позже."
                )
        
        return (
            f"👤 <b>Никнейм:</b> {username}\n"
            f"💵 <b>Баланс:</b> {balance} руб.\n"
            f"🆔 <b>User ID:</b> {user_id}\n"
            f"🔑 <b>UUID:</b> <code>{uuid}</code>"
        )
    
    @staticmethod
    def has_active_subscription(user_id: int) -> bool:
        """
        Проверить наличие активной подписки.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True если есть активная подписка
        """
        user = db.get_user(user_id)
        if not user:
            return False
        
        uuid = user[2]
        return bool(uuid and uuid != "N/A")
    
    @staticmethod
    def can_renew_subscription(user_id: int) -> bool:
        """
        Проверить возможность продления подписки.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True если можно продлить подписку
        """
        user = db.get_user(user_id)
        if not user or not user[3]:
            return False
        
        try:
            profile = json.loads(user[3])
            balance = profile.get("balance", 0)
            tariff = profile.get("ticket_tariff")
            
            if not tariff:
                return False
            
            charge_amount = tariff.get("price", 0)
            return balance >= charge_amount
            
        except (json.JSONDecodeError, TypeError):
            return False
