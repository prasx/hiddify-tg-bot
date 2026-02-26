import os
import database as db

def is_admin(user_id):
    return user_id in db.get_admins()


class BotConfig:
    """Конфигурация Telegram бота"""
    ADMIN_PAYMENTS = 12345678
    TOKEN = ""  # API_TOKEN бота

class HiddifyConfig:
    """Конфигурация Hiddify API и сервера"""
    BASE_URL = "https://your-hiddify-domain.com"
    ADMIN_PATH = "/your-admin-path"
    USER_PATH = "/your-user-path"
    API_KEY = "your-api-key"  # Ключ API из панели Hiddify
    
    @classmethod
    def get_api_url(cls):
        """Полный URL для API"""
        return f"{cls.BASE_URL}{cls.ADMIN_PATH}/"
    
    @classmethod
    def get_user_link(cls, uuid: str):
        """Ссылка на конфигурацию пользователя"""
        return f"{cls.BASE_URL}{cls.USER_PATH}/{uuid}/"
    
    @classmethod
    def get_proxy_stats_url(cls):
        """Ссылка на статистику прокси"""
        return f"{cls.BASE_URL}{cls.ADMIN_PATH}/proxy-stats/api"


class TariffConfig:
    """Тарифные планы"""
    TARIFFS = {
        "30day": {"package_days": 30, "usage_limit_GB": 130, "price": 400, "emoji": "🤏"},
        "60day": {"package_days": 60, "usage_limit_GB": 370, "price": 800, "emoji": "👍"},
        "90day": {"package_days": 90, "usage_limit_GB": 690, "price": 1200, "emoji": "🤘"},
    }