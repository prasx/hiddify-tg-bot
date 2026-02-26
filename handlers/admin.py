"""
Админские обработчики.
"""

import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

import database as db
from services.payment_service import PaymentService


logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith("confirm_payment_to_admin"))
async def confirm_payment_admin(callback_query: CallbackQuery):
    """
    Подтверждение оплаты админом.
    
    Обработчик для кнопки подтверждения платежа от админа.
    """
    # Парсим данные из callback
    _, user_id, duration = callback_query.data.split("-")
    user_id = int(user_id)
    
    # Пополняем баланс
    db.add_balance(user_id)
    
    # Отправляем уведомление пользователю
    user_message = f"✅ Ваш платеж подтвержден! Подписка на {duration} активирована."
    await callback_query.message.bot.send_message(user_id, user_message, parse_mode="HTML")
    
    # Редактируем сообщение админа
    await callback_query.message.edit_text(
        f"💰 Баланс пользователя {user_id} пополнен. Подписка на {duration} активирована.",
        reply_markup=None
    )
    
    logger.info(f"Платёж пользователя {user_id} подтверждён админом")
