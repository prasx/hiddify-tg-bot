"""
Сервис для управления подписками.
"""

import json
import logging
from typing import Optional, Dict, Any

from aiogram import Bot

import database as db
from services.hiddify_service import HiddifyService


logger = logging.getLogger(__name__)


class SubscriptionService:
    """Сервис для управления подписками пользователей."""
    
    def __init__(self, bot: Bot, hiddify_service: HiddifyService):
        """
        Инициализация сервиса подписок.
        
        Args:
            bot: Экземпляр бота
            hiddify_service: Сервис для работы с Hiddify API
        """
        self.bot = bot
        self.hiddify = hiddify_service
        logger.info("SubscriptionService инициализирован")
    
    async def create_subscription(
        self,
        user_id: int,
        username: str,
        package_days: int,
        usage_limit_GB: int,
        service_cost: float
    ) -> Dict[str, Any]:
        """
        Создать новую подписку для пользователя.

        Args:
            user_id: Telegram ID пользователя
            username: Имя пользователя
            package_days: Срок подписки в днях
            usage_limit_GB: Лимит трафика в GB
            service_cost: Стоимость услуги

        Returns:
            dict с результатом операции
        """
        # Получаем профиль пользователя
        user = db.get_user(user_id)
        if not user or not user[3]:
            return {"error": "Пользователь не найден"}
        
        try:
            profile = json.loads(user[3])
        except json.JSONDecodeError:
            return {"error": "Ошибка профиля пользователя"}
        
        current_balance = profile.get('balance', 0.0)
        
        # Проверяем баланс
        if current_balance < service_cost:
            return {"error": "Недостаточно средств на балансе"}
        
        # Списываем средства
        new_balance = current_balance - service_cost
        profile['balance'] = new_balance
        db.update_user_profile(user_id, json.dumps(profile))
        
        # Создаём профиль name для Hiddify
        profile_name = f"{username}-{user_id}"
        
        # Регистрируем в Hiddify
        response = self.hiddify.create_user(
            name=profile_name,
            telegram_id=user_id,
            package_days=package_days,
            usage_limit_GB=usage_limit_GB
        )
        
        if "uuid" in response:
            new_uuid = response["uuid"]
            db.update_user_uuid(user_id, new_uuid)
            logger.info(f"Подписка создана для пользователя {user_id}, UUID: {new_uuid}")
            
            return {
                "success": True,
                "uuid": new_uuid,
                "new_balance": new_balance,
                "package_days": package_days
            }
        else:
            error_message = response.get("error", "Неизвестная ошибка при регистрации в Hiddify")
            logger.error(f"Ошибка регистрации в Hiddify: {error_message}")
            return {"error": error_message}
    
    async def reset_traffic(self, user_id: int) -> Dict[str, Any]:
        """
        Сбросить трафик и продлить подписку пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            dict с результатом операции
        """
        user_info = db.get_user(user_id)
        if not user_info:
            return {"error": "Пользователь не найден"}
        
        uuid = user_info[2]
        if not uuid or uuid == "N/A":
            return {"error": "Нет активной подписки"}
        
        # Получаем данные профиля
        try:
            profile_data = json.loads(user_info[3])
        except json.JSONDecodeError:
            return {"error": "Ошибка профиля пользователя"}
        
        balance = profile_data.get("balance", 0)
        ticket_tariff = profile_data.get("ticket_tariff", {})
        
        charge_amount = ticket_tariff.get("price")
        package_days = ticket_tariff.get("package_days")
        
        if charge_amount is None or package_days is None:
            return {"error": "Не удалось определить стоимость или продолжительность подписки"}
        
        if balance < charge_amount:
            return {"error": "Недостаточно средств для продления"}
        
        # Списываем средства
        profile_data["balance"] -= charge_amount
        db.update_user_profile(user_id, json.dumps(profile_data))
        
        # Сбрасываем трафик в Hiddify
        response = self.hiddify.reset_traffic(uuid, package_days)
        
        if response.get("message") != "Сброс не требуется":
            logger.info(f"Трафик сброшен для пользователя {user_id}")
            return {
                "success": True,
                "new_balance": profile_data["balance"],
                "charge_amount": charge_amount,
                "package_days": package_days
            }
        else:
            return {"message": "Сброс не требуется"}
    
    def get_tariff_from_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить тариф из профиля пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            dict с тарифом или None
        """
        user = db.get_user(user_id)
        if not user or not user[3]:
            return None
        
        try:
            profile = json.loads(user[3])
            return profile.get("ticket_tariff")
        except (json.JSONDecodeError, TypeError):
            return None
    
    def save_tariff_to_profile(self, user_id: int, tariff: Dict[str, Any]) -> None:
        """
        Сохранить тариф в профиль пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            tariff: Данные тарифа
        """
        db.update_user_tariff(user_id, tariff)
        logger.info(f"Тариф сохранён для пользователя {user_id}")
    
    def clear_tariff_from_profile(self, user_id: int) -> None:
        """
        Удалить тариф из профиля пользователя.
        
        Args:
            user_id: Telegram ID пользователя
        """
        db.clear_user_tariff(user_id)
        logger.info(f"Тариф удалён из профиля пользователя {user_id}")
    
    def get_subscription_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о подписке пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            dict с информацией о подписке или None
        """
        user = db.get_user(user_id)
        if not user or not user[2] or user[2] == "N/A":
            return None
        
        uuid = user[2]
        hiddify_info = self.hiddify.get_user_info(uuid)
        
        if "error" in hiddify_info:
            return None
        
        return hiddify_info
