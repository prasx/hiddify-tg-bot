"""
Обработчики команд Telegram бота.
"""

import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

import database as db
import config
from keyboards.main_menu import main_menu_buttons
from services.user_service import UserService
from handlers.callbacks import hiddify_service


logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start.
    Регистрирует нового пользователя или показывает главное меню.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    # Обновляем позицию
    db.update_pos("start", user_id)

    # Проверяем, существует ли пользователь
    user = db.get_user(user_id)

    if not user:
        # Регистрируем нового пользователя
        db.add_user(user_id, username)
        logger.info(f"Пользователь {username} (ID: {user_id}) зарегистрирован.")

        text = (
            "<b>Добро пожаловать! </b>🌐\n\n"
            "Я бот, который поможет вам обезопасить ваш интернет-трафик и выйти за рамки ограничений.\n\n"
            "❗️Первым делом установите наше приложение, нажав на кнопку <b>📱Установить App</b> ниже.\n\n"
        )
    else:
        # Показываем полную информацию о пользователе (как в главном меню)
        # Используем глобальный сервис из callbacks (с общим кэшем)
        # Если сервис ещё не инициализирован, создаём временный
        service = hiddify_service
        if service is None:
            from services.hiddify_service import HiddifyService
            service = HiddifyService()
        text = UserService.get_user_info_text(user_id, service)

    keyboard = main_menu_buttons(user_id)
    await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")


@router.message(Command("msg_all"))
async def cmd_msg_all(message: Message):
    """
    Обработчик команды /msg_all для рассылки сообщений всем пользователям.
    Доступно только администраторам.
    """
    admin_ids = [config.BotConfig.ADMIN_PAYMENTS]
    
    if message.from_user.id not in admin_ids:
        await message.reply("🤷‍♂️ У вас нет прав для выполнения этой команды.", parse_mode="HTML")
        return
    
    # Извлекаем текст сообщения после команды
    broadcast_message = message.text[len("/msg_all "):].strip()
    
    if not broadcast_message:
        await message.reply("А как же сообщение ⁉️💬\nПосле команды /msg_all.")
        return
    
    # Получаем всех пользователей
    users = db.get_all_user_ids()
    
    successful_deliveries = []
    failed_deliveries = []
    
    # Отправляем сообщение каждому пользователю
    for user_id in users:
        try:
            await message.bot.send_message(user_id, broadcast_message, parse_mode="HTML")
            successful_deliveries.append(user_id)
        except Exception as e:
            failed_deliveries.append((user_id, str(e)))
            logger.warning(f"Не удалось доставить сообщение пользователю {user_id}: {e}")
    
    # Формируем отчёт
    summary_message = (
        f"‼️ Рассылка завершена.\n\n"
        f"✅ Успешно доставлено: {len(successful_deliveries)} пользователям.\n"
        f"❌ Не удалось доставить: {len(failed_deliveries)} пользователям.\n"
    )
    
    if failed_deliveries:
        summary_message += "\n<b>😱 Список пользователей, которым не удалось доставить сообщение:</b>\n"
        for user_id, error in failed_deliveries[:20]:  # Ограничиваем вывод
            summary_message += f"ID: {user_id}, Ошибка: {error}\n"
        if len(failed_deliveries) > 20:
            summary_message += f"... и ещё {len(failed_deliveries) - 20} пользователей"
    
    await message.reply(summary_message, parse_mode="HTML")
