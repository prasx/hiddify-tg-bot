"""
Сервис для взаимодействия с Hiddify API.
Обёртка над HiddifyAPI с бизнес-логикой и кэшированием.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import config
from hiddify_api import HiddifyAPI


logger = logging.getLogger(__name__)


class HiddifyService:
    """Сервис для взаимодействия с Hiddify API."""

    def __init__(self, cache_ttl_seconds: int = 30):
        self.api = HiddifyAPI(
            api_url=config.HiddifyConfig.get_api_url(),
            api_key=config.HiddifyConfig.API_KEY
        )
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(seconds=cache_ttl_seconds)
        logger.info(f"HiddifyService инициализирован (кэш TTL: {cache_ttl_seconds}с)")

    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Получить данные из кэша, если они не устарели."""
        if key in self._cache:
            cached = self._cache[key]
            if datetime.now() - cached['timestamp'] < self._cache_ttl:
                return cached['data']
            else:
                del self._cache[key]
        return None

    def _set_cached(self, key: str, data: Dict[str, Any]):
        """Сохранить данные в кэш."""
        self._cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        # Очищаем старые записи (раз в 100 запросов)
        if len(self._cache) > 100:
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Очистить устаревшие записи кэша."""
        now = datetime.now()
        expired = [k for k, v in self._cache.items() 
                   if now - v['timestamp'] >= self._cache_ttl]
        for key in expired:
            del self._cache[key]

    def get_user_info(self, uuid: str, use_cache: bool = True) -> dict:
        """
        Получить информацию о пользователе с форматированием данных.

        Args:
            uuid: UUID пользователя
            use_cache: Использовать ли кэш (по умолчанию True)

        Returns:
            dict с информацией о пользователе
        """
        # Проверяем кэш
        cache_key = f"user:{uuid}"
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                logger.debug(f"Кэш хит для {uuid}")
                return cached

        # Запрос к API
        logger.debug(f"Запрос к API для {uuid}")
        response = self.api.get_user(uuid)

        if "error" in response:
            return {"error": response["error"]}

        # Вычисляем дату окончания
        expire_date = self._calculate_expire_date(response)

        result = {
            "status": "Активен" if response.get('is_active') else "Неактивен",
            "start_date": response.get('start_date', 'Неизвестно'),
            "expire_date": expire_date,
            "current_usage_gb": float(response.get('current_usage_GB', 0)),
            "usage_limit_gb": response.get('usage_limit_GB', 'N/A'),
            "last_online": response.get('last_online', "Неизвестно"),
            "link": config.HiddifyConfig.get_user_link(uuid),
            "package_days": int(response.get('package_days', 0)),
        }

        # Сохраняем в кэш
        self._set_cached(cache_key, result)

        return result

    def _calculate_expire_date(self, user_data: dict) -> str:
        """
        Вычислить дату окончания подписки.

        Args:
            user_data: Данные пользователя от API

        Returns:
            Строка с датой окончания или 'Неизвестно'
        """
        package_days = int(user_data.get('package_days', 0))
        if package_days <= 0:
            return 'Неизвестно'

        # Пытаемся найти дату начала периода
        current_period_start = None
        for field in ('last_reset_time', 'period_start', 'last_online', 'start_date'):
            val = user_data.get(field)
            if val and val not in ('Неизвестно', None):
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt = datetime.strptime(val, fmt)
                        current_period_start = dt
                        break
                    except Exception:
                        continue
                if current_period_start:
                    break

        if current_period_start:
            expire_date = current_period_start + timedelta(days=package_days)
            return expire_date.strftime("%Y-%m-%d")

        return 'Неизвестно'

    def create_user(self, name: str, telegram_id: int, package_days: int, usage_limit_GB: int) -> dict:
        """
        Создать нового пользователя в Hiddify.

        Args:
            name: Имя пользователя
            telegram_id: Telegram ID
            package_days: Срок подписки в днях
            usage_limit_GB: Лимит трафика в GB

        Returns:
            dict с результатом операции
        """
        logger.info(f"Создание пользователя {name} (TG ID: {telegram_id})")
        logger.info(f"Параметры: package_days={package_days}, usage_limit_GB={usage_limit_GB}")

        response = self.api.create_new_bill(
            name=name,
            telegram_id=telegram_id,
            package_days=package_days,
            usage_limit_GB=usage_limit_GB
        )

        logger.info(f"Ответ от Hiddify API: {response}")
        
        # Очищаем кэш при создании нового пользователя
        cache_key = f"user:{response.get('uuid', '')}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        return response

    def reset_traffic(self, uuid: str, package_days: int) -> dict:
        """
        Сбросить трафик пользователя и обновить дату начала.

        Args:
            uuid: UUID пользователя
            package_days: Срок подписки в днях

        Returns:
            dict с результатом операции
        """
        logger.info(f"Сброс трафика для пользователя {uuid}")

        response = self.api.reset_user_traffic(
            uuid=uuid,
            mode="monthly",
            last_reset_time=None,
            package_days=package_days
        )

        # Очищаем кэш для этого пользователя
        cache_key = f"user:{uuid}"
        if cache_key in self._cache:
            del self._cache[cache_key]

        return response

    def get_users_list(self) -> list:
        """
        Получить список всех пользователей.

        Returns:
            list с информацией о пользователях
        """
        return self.api.get_users()

    def get_subscription_link(self, uuid: str, user_id: int, username: str) -> str:
        """
        Получить ссылку на подписку пользователя.

        Args:
            uuid: UUID пользователя
            user_id: Telegram ID пользователя
            username: Имя пользователя

        Returns:
            Строка с ссылкой на подписку
        """
        return (
            f"{config.HiddifyConfig.BASE_URL}{config.HiddifyConfig.USER_PATH}/{uuid}/sub/"
            f"?asn=unknown#{username}-{user_id}"
        )
