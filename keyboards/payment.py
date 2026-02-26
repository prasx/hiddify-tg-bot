"""
Клавиатуры для платежей.
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder


def confirm_payment_button(user_id: int) -> InlineKeyboardBuilder:
    """
    Кнопка подтверждения оплаты.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        InlineKeyboardBuilder с кнопками
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="💵 Подтвердить оплату", callback_data="confirm_payment")
    builder.button(text="◀️ Назад", callback_data="reg_subscription")
    return builder


def confirm_payment_button_done(user_id: int) -> InlineKeyboardBuilder:
    """
    Кнопка после подтверждения оплаты.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        InlineKeyboardBuilder с кнопкой назад
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="reg_subscription")
    return builder


def admin_payment_buttons(user_id: int) -> InlineKeyboardBuilder:
    """
    Админские кнопки для пополнения баланса пользователя.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        InlineKeyboardBuilder с кнопками сумм
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="Пополнить на 400 руб.", callback_data=f"admin_balance_{user_id}_400")
    builder.button(text="Пополнить на 800 руб.", callback_data=f"admin_balance_{user_id}_800")
    builder.button(text="Пополнить на 1200 руб.", callback_data=f"admin_balance_{user_id}_1200")
    builder.button(text="Отменить", callback_data="cancel_payment")
    builder.adjust(2, 2)
    return builder
