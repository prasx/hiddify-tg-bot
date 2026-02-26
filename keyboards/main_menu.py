"""
Клавиатуры главного меню.
"""

import json
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
import config


def main_menu_back() -> InlineKeyboardBuilder:
    """Кнопка 'Назад' для возврата в главное меню."""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="main_menu")
    return builder


def main_menu_buttons(user_id: int) -> InlineKeyboardBuilder:
    """
    Основное меню бота.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        InlineKeyboardBuilder с кнопками меню
    """
    builder = InlineKeyboardBuilder()
    user_info = db.get_user(user_id)
    uuid = user_info[2] if user_info and user_info[2] and user_info[2] != "N/A" else None

    if uuid:
        builder.button(text="🔗 Получить профиль", callback_data="choose_profile")
        
        # Проверяем баланс и тариф для возможности обновления
        profile_data = None
        if user_info and user_info[3]:
            try:
                profile_data = json.loads(user_info[3])
            except Exception:
                pass
        
        balance = profile_data.get("balance", 0) if profile_data else 0
        ticket_tariff = profile_data.get("ticket_tariff", {}) if profile_data else {}
        charge_amount = ticket_tariff.get("price")

        if charge_amount is not None and balance >= charge_amount:
            builder.button(text="🔄 Обновить подписку", callback_data="reset_traffic")
        else:
            builder.button(text="💵 Пополнить баланс", callback_data="reg_subscription")
    else:
        builder.button(text="❤️ Зарегестрироваься", callback_data="reg_subscription")

    builder.button(text="📱 Установить App", callback_data="download_app")

    # Админские кнопки
    if config.is_admin(user_id):
        builder.button(text="📜 Пользователи", callback_data="get_users")
        builder.button(text="📋 Proxy", url=config.HiddifyConfig.get_proxy_stats_url())

    builder.adjust(1)
    return builder


def connect_buttons(user_id: int) -> InlineKeyboardBuilder:
    """
    Кнопки подключения.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        InlineKeyboardBuilder с кнопками подключения
    """
    builder = InlineKeyboardBuilder()
    user_info = db.get_user(user_id)
    uuid = user_info[2] if user_info and user_info[2] and user_info[2] != "N/A" else None

    if uuid:
        builder.button(text="🔄 Сбросить трафик", callback_data="reset_traffic")
        builder.button(text="◀️ В главное меню", callback_data="main_menu")
    else:
        builder.button(text="✔️ Окей", callback_data="connect")

    return builder


def balance_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура для пополнения баланса."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Пополнить баланс", callback_data="add_balance_30day")
    builder.button(text="Назад", callback_data="main_menu")
    return builder
