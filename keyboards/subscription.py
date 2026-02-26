"""
Клавиатуры для работы с подписками.
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_buttons() -> InlineKeyboardBuilder:
    """
    Клавиатура выбора тарифа.
    
    Returns:
        InlineKeyboardBuilder с кнопками тарифов
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🤏 30 дней / 400 рублей", callback_data="add_balance_30day")
    builder.button(text="👍 60 дней / 800 рублей", callback_data="add_balance_60day")
    builder.button(text="🤘 90 дней / 1200 рублей", callback_data="add_balance_90day")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder


def subscription_action_buttons(balance: float, charge_amount: float | None) -> InlineKeyboardBuilder:
    """
    Клавиатура действий с подпиской в зависимости от баланса.
    
    Args:
        balance: Текущий баланс пользователя
        charge_amount: Стоимость подписки
        
    Returns:
        InlineKeyboardBuilder с кнопками действий
    """
    builder = InlineKeyboardBuilder()
    
    if charge_amount is not None and balance >= charge_amount:
        builder.button(text="🔄 Обновить подписку", callback_data="reset_traffic")
    else:
        builder.button(text="💵 Пополнить баланс", callback_data="reg_subscription")
    
    return builder
