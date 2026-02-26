"""
Обработчики текстовых сообщений и медиа.
"""

import json
import logging

from aiogram import Router, F
from aiogram.types import Message

import database as db
import config


logger = logging.getLogger(__name__)

router = Router()


@router.message(F.chat.type == "private")
async def handle_message(message: Message):
    """
    Обработчик текстовых сообщений.
    Пересылает сообщения админу если пользователь в режиме подтверждения оплаты.
    """
    await forward_to_admin(message)


@router.message(F.content_type.in_({"photo", "document"}))
async def handle_media(message: Message):
    """
    Обработчик медиа (фото, документы).
    Пересылает медиа админу если пользователь в режиме подтверждения оплаты.
    """
    await forward_to_admin(message)


async def forward_to_admin(message: Message):
    """
    Переслать сообщение пользователя админу.
    
    Args:
        message: Сообщение от пользователя
    """
    user_id = message.from_user.id
    user = db.get_user(user_id)
    pos = user[4] if user else "start"

    # Пересылаем только если пользователь в режиме подтверждения оплаты
    if pos == "confirm_payment":
        admin_id = config.BotConfig.ADMIN_PAYMENTS
        
        if message.text:
            admin_message = f"Пользователь @{message.from_user.username} (ID: {user_id}) отправил текст: {message.text}"
            await message.bot.send_message(admin_id, admin_message)
        elif message.photo:
            admin_message = f"Пользователь @{message.from_user.username} (ID: {user_id}) отправил скриншот оплаты."
            await message.bot.send_message(admin_id, admin_message)
            await message.bot.send_photo(admin_id, message.photo[-1].file_id)
        elif message.document:
            admin_message = f"Пользователь @{message.from_user.username} (ID: {user_id}) отправил документ оплаты."
            await message.bot.send_message(admin_id, admin_message)
            await message.bot.send_document(admin_id, message.document.file_id)
