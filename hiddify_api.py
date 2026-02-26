import database
import requests
import config 
import json
import logging
from datetime import datetime, timedelta

class HiddifyAPI:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "Accept": "application/json",
            "Hiddify-API-Key": api_key,
        }
        logging.info(f"HiddifyAPI инициализирован с URL: {self.api_url}")
        logging.info(f"API Key: {api_key[:10]}...")


    def _request(self, method, endpoint, params=None, data=None):
        url = f"{self.api_url}/{endpoint}"
        logging.info(f"API Request: {method} {url}")
        if data:
            logging.info(f"Request data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        try:
            response = requests.request(
                method, url, 
                headers=self.headers, 
                params=params, 
                json=data,
                timeout=10  # Таймаут 10 секунд
            )
            
            logging.info(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logging.error(f"Error {response.status_code}: {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            
            return response.json()
        except requests.exceptions.Timeout:
            logging.error(f"Timeout при запросе к {url}")
            return {"error": "Превышено время ожидания ответа от сервера"}
        except requests.exceptions.ConnectionError:
            logging.error(f"Ошибка соединения с {url}")
            return {"error": "Ошибка соединения с сервером"}
        except Exception as e:
            logging.error(f"Неожиданная ошибка при запросе: {e}")
            return {"error": f"Ошибка: {str(e)}"}


    def get_users(self):
        """Получить список всех пользователей и их характеристики (трафик, дата, статус и т. д.)"""
        response = self._request("GET", "api/v2/admin/user/")
        logging.info(f"Ответ API /get_users:\n{json.dumps(response, indent=4, ensure_ascii=False)}")
    
        # Проверяем на наличие ошибки
        if not isinstance(response, list):
            return response.get("error", "Неизвестная ошибка")
        # Формируем список с расширенной информацией
        users_info = []
        for user in response:
            name = user.get("name", "Неизвестно")
            uuid = user.get("uuid", "N/A")
            total_usage = round(user.get("current_usage_GB", 0), 2)  # Использованный трафик (в GB)
            usage_limit = user.get("usage_limit_GB", "∞")  # Лимит трафика
            last_online = user.get("last_online", "Нет данных")  # Последняя активность
            mode = user.get("mode", "N/A")  # Режим тарифа
            package_days = user.get("package_days", "N/A")  # Срок подписки (в днях)
            start_date = user.get("start_date", "N/A")  # Дата начала подписки
            is_active = user.get("is_active", False)  # Активен или нет
            active_status = "✅ Активен" if is_active else "❌ Неактивен"

            users_info.append(
                f"👨‍🦱 @{name}\n"
                f"📊 Использовано: {total_usage} GB / {usage_limit} GB\n"
                f"📅 Подписка: {start_date} ({package_days} дней)\n"
                f"🔄 Тариф: {mode}\n"
                f"🕒 Последний онлайн: {last_online}\n"
                f"🔹 Статус: {active_status}"
            )
        return users_info


    def create_new_bill(self, name: str, telegram_id: int, package_days: int, usage_limit_GB: int):
        """Создать нового пользователя с заданным сроком подписки и лимитом трафика"""
        data = {
            "name": name,
            "telegram_id": telegram_id,
            "enable": True,
            "is_active": True,
            "usage_limit_GB": usage_limit_GB,  # Лимит трафика
            "mode": "monthly",
            "package_days": package_days,  # Срок подписки
        }
        return self._request("POST", "api/v2/admin/user/", data=data)


    def get_user(self, uuid: str):
        """Получить информацию о пользователе по UUID"""
        response = self._request("GET", f"api/v2/admin/user/{uuid}/")
        logging.info(f"Ответ API /get_users:\n{json.dumps(response, indent=4, ensure_ascii=False)}")

        if "error" in response:
            return {"error": response["error"]}

        user_data = response
        link = config.HiddifyConfig.get_user_link(uuid)
        current_usage_GB = float(user_data.get('current_usage_GB', 0))
        usage_limit_GB = user_data.get('usage_limit_GB', 'N/A')
        package_days = int(user_data.get('package_days', 0))

        # date_reg — это просто дата в базе, для совместимости возвращаем её как start_date
        date_reg = user_data.get('start_date', 'Неизвестно')

        # Для фактического старта стараемся использовать last_reset_time, затем last_online, затем дату регистрации
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
        if current_period_start and package_days > 0:
            expire_date = (current_period_start + timedelta(days=package_days)).strftime("%Y-%m-%d")
            current_period_start_str = current_period_start.strftime("%Y-%m-%d")
        else:
            expire_date = 'Неизвестно'
            current_period_start_str = None
        user_info = {
            "status": "Активен" if user_data.get('is_active') else "Неактивен",
            "start_date": date_reg,
            "current_period_start": current_period_start_str,
            "expire_date": expire_date,
            "current_usage_GB": current_usage_GB,
            "usage_limit_GB": usage_limit_GB,
            "last_online": user_data.get('last_online', "Неизвестно"),
            "link": link,
            "package_days": package_days,
        }
        return user_info


    def reset_user_traffic(self, uuid: str, mode: str, last_reset_time: str, package_days: int):
        """Сбрасывает трафик и обновляет дату начала услуги"""
        now = datetime.now()
        data = {
            "current_usage_GB": 0,
            "last_reset_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "start_date": now.strftime("%Y-%m-%d"),
            "package_days": package_days,
        }
        return self._request("PATCH", f"api/v2/admin/user/{uuid}/", data=data)


    # Дополнительная логика взаимодействия с API требует доработки
    def delete_user(self, uuid: str):
        """Удалить пользователя по UUID"""
        return self._request("DELETE", f"api/v2/admin/user/{uuid}/")

    def get_user_config(self, uuid: str):
        """Получить конфигурацию пользователя"""
        return self._request("GET", f"api/v2/user/all-configs/{uuid}/")

    def get_domains(self):
        """Получить список доступных доменов/SNI"""
        try:
            response = self._request("GET", "api/v2/admin/domain/")
            logging.info(f"Ответ API /get_domains:\n{json.dumps(response, indent=4, ensure_ascii=False)}")
            return response
        except Exception as e:
            logging.error(f"Ошибка при получении доменов: {e}")
            return []
    
    def get_all_configs(self):
        """Получить все доступные конфигурации сервера"""
        try:
            # Пробуем разные эндпоинты
            endpoints = [
                "api/v2/admin/domain/",
                "api/v2/admin/config/",
                "api/v2/admin/settings/",
            ]
            
            for endpoint in endpoints:
                try:
                    response = self._request("GET", endpoint)
                    logging.info(f"Ответ от {endpoint}:\n{json.dumps(response, indent=4, ensure_ascii=False)}")
                    return response
                except:
                    continue
            
            return None
        except Exception as e:
            logging.error(f"Ошибка при получении конфигураций: {e}")
            return None
