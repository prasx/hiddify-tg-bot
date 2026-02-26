"""
Обработчики callback query Telegram бота.
"""

import json
import logging
import traceback

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
import database as db
from keyboards.main_menu import main_menu_buttons, main_menu_back, connect_buttons
from keyboards.subscription import subscription_buttons, subscription_action_buttons
from keyboards.payment import confirm_payment_button, confirm_payment_button_done
from keyboards.profile import profile_type_keyboard, install_app_button_hiddify, install_app_button_v2ray, client_type_keyboard
from services.user_service import UserService
from services.payment_service import PaymentService
from services.subscription_service import SubscriptionService
from services.hiddify_service import HiddifyService
from services.notification_service import NotificationService


logger = logging.getLogger(__name__)

router = Router()

# Инициализация сервисов (будут переданы из main.py)
hiddify_service = None
payment_service = None
subscription_service = None
notification_service = None


def init_services(bot):
    """Инициализировать сервисы для использования в обработчиках."""
    global hiddify_service, payment_service, subscription_service, notification_service
    
    hiddify_service = HiddifyService()
    payment_service = PaymentService(bot)
    subscription_service = SubscriptionService(bot, hiddify_service)
    notification_service = NotificationService(bot, hiddify_service)


@router.callback_query()
async def handle_callback(callback_query: CallbackQuery):
    """
    Основной обработчик callback query.
    Маршрутизирует запросы по типам данных.
    """
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    logging.info(f"Получен callback: {data} от пользователя {user_id}")
    db.update_pos(data, user_id)

    try:
        # Главное меню
        if data == "main_menu":
            await callback_query.answer()
            await handle_main_menu(callback_query)

        # Подключение
        elif data == "connect":
            await callback_query.answer()
            await handle_connect(callback_query)

        # Выбор профиля
        elif data == "choose_profile":
            await callback_query.answer()
            await handle_choose_profile(callback_query)

        # Получение ссылок
        elif data == "link_v2ray":
            await callback_query.answer()
            await handle_link_v2ray(callback_query)

        elif data == "link_hiddify":
            await callback_query.answer()
            await handle_link_hiddify(callback_query)

        # Скачивание приложения
        elif data == "download_app":
            await callback_query.answer()
            await handle_download_app(callback_query)

        elif data == "download_app_hiddify":
            await callback_query.answer()
            await handle_download_app_hiddify(callback_query)

        elif data == "download_app_v2ray":
            await callback_query.answer()
            await handle_download_app_v2ray(callback_query)

        # Подписки и оплата
        elif data == "reg_subscription":
            logging.info("Обработка reg_subscription")
            await callback_query.answer()
            await handle_reg_subscription(callback_query)

        elif data.startswith("add_balance_"):
            await callback_query.answer()
            await handle_add_balance(callback_query)

        elif data == "confirm_payment":
            await callback_query.answer()
            await handle_confirm_payment(callback_query)

        elif data.startswith('admin_balance_'):
            await callback_query.answer()
            await handle_admin_balance(callback_query)

        elif data == "cancel_payment":
            await callback_query.answer()
            await handle_cancel_payment(callback_query)

        # Сброс трафика
        elif data == "reset_traffic":
            await callback_query.answer()
            await show_reset_traffic_confirmation(callback_query)

        elif data == "confirm_reset_traffic":
            await callback_query.answer()
            await handle_confirm_reset_traffic(callback_query)

        elif data == "cancel_reset_traffic":
            await callback_query.answer("Отменено")
            await handle_main_menu(callback_query)

        # Админские функции
        elif data == "get_users":
            await callback_query.answer()
            await handle_get_users(callback_query)

        else:
            logger.warning(f"Неизвестный callback: {data}")
            await callback_query.answer("Неизвестная команда")

    except Exception as e:
        logger.error(f"Ошибка в handle_callback: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        await callback_query.answer("Произошла ошибка. Попробуйте позже.")


async def handle_main_menu(callback_query: CallbackQuery):
    """Обработчик главного меню."""
    user_id = callback_query.from_user.id
    text = UserService.get_user_info_text(user_id, hiddify_service)
    await callback_query.message.edit_text(text, reply_markup=main_menu_buttons(user_id).as_markup(), parse_mode="HTML")


async def handle_connect(callback_query: CallbackQuery):
    """Обработчик подключения."""
    user_id = callback_query.from_user.id
    balance = UserService.get_user_balance(user_id)

    if balance == 0:
        from keyboards.main_menu import balance_keyboard
        await callback_query.message.edit_text(
            "Ваш баланс равен 0. Пожалуйста, пополните баланс.",
            reply_markup=balance_keyboard().as_markup()
        )
    else:
        await callback_query.answer("Пожалуйста, подождите...")
        await handle_user_connection(callback_query.message, user_id)


async def handle_choose_profile(callback_query: CallbackQuery):
    """Выбор типа профиля."""
    text = (
        "<b>🔗 Выберите тип профиля:</b>\n\n"
        "📱 <b>Hiddify</b> - Универсальная ссылка для приложения Hiddify\n"
        "📱 <b>V2Ray</b> - Конфигурация для приложения V2Ray\n"
    )
    await callback_query.message.edit_text(text, reply_markup=profile_type_keyboard().as_markup(), parse_mode="HTML")


async def handle_link_v2ray(callback_query: CallbackQuery):
    """Получение V2Ray ссылки."""
    user_id = callback_query.from_user.id
    user_info = db.get_user(user_id)
    uuid = user_info[2] if user_info and user_info[2] and user_info[2] != "N/A" else None

    # Получаем информацию о подписке
    profile_data = json.loads(user_info[3]) if user_info[3] else {}
    balance = profile_data.get("balance", 0)
    username = profile_data.get("username", "user")

    # Формируем ссылку на подписку
    subscription_link = hiddify_service.get_subscription_link(uuid, user_id, username)

    # Получаем данные с Hiddify API
    try:
        hiddify_info = hiddify_service.get_user_info(uuid)
        if isinstance(hiddify_info, dict) and 'error' not in hiddify_info:
            usage_gb = hiddify_info.get('current_usage_gb', 0)
            limit_gb = hiddify_info.get('usage_limit_gb', 0)
            expire_date = hiddify_info.get('expire_date', 'Неизвестно')
        else:
            usage_gb = 0
            limit_gb = 0
            expire_date = 'Неизвестно'
    except Exception as e:
        logger.error(f"Ошибка при получении данных пользователя: {e}")
        usage_gb = 0
        limit_gb = 0
        expire_date = 'Неизвестно'

    text = (
        f"🌐 <b>V2Ray конфигурация</b>\n\n"
        f"📊 <b>Статус подписки:</b>\n"
        f"💰 Баланс: {balance} руб.\n"
        f"📈 Использовано: {usage_gb:.2f} GB / {limit_gb} GB\n"
        f"📅 Действует до: {expire_date}\n\n"
        f"🔗 <b>Ссылка на подписку:</b>\n\n"
        f"<code>{subscription_link}</code>\n\n"
        f"✨ Нажмите на ссылку выше для копирования\n\n"
        f"📝 <b>Инструкция:</b>\n"
        f"1. Скопируйте ссылку выше\n"
        f"2. Откройте V2Ray приложение\n"
        f"3. Добавьте подписку через меню\n"
        f"4. Вставьте скопированную ссылку\n"
        f"5. Обновите список серверов\n\n"
        f"⚠️ <b>ПРИМЕЧАНИЕ:</b> После импорта добавьте исключения для доменов "
        f"<b>.ru</b>, <b>.рф</b> и <b>.su</b>"
    )

    await callback_query.message.edit_text(text, reply_markup=main_menu_back().as_markup(), parse_mode="HTML")


async def handle_link_hiddify(callback_query: CallbackQuery):
    """Получение Hiddify ссылки."""
    user_id = callback_query.from_user.id
    user_info = db.get_user(user_id)
    uuid = user_info[2] if user_info and user_info[2] and user_info[2] != "N/A" else None
    link = config.HiddifyConfig.get_user_link(uuid)

    text = (
        f"🌐 <b>Hiddify конфигурация</b>\n\n"
        f"Нажмите на кнопку ниже, чтобы открыть все доступные конфигурации в приложении Hiddify.\n\n"
        f"📝 <b><i>ПРИМЕЧАНИЕ:</i></b> Убедитесь, что у вас установлено приложение Hiddify. "
        f"Если нет, вернитесь назад и установите его."
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⚙️ Открыть конфигурации Hiddify", url=link)
    keyboard.button(text="◀️ Назад", callback_data="choose_profile")
    keyboard.adjust(1)
    
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")


async def handle_download_app(callback_query: CallbackQuery):
    """Выбор клиента для скачивания."""
    text = (
        "<b>🤔 Выберите клиент, который будете использовать:</b>\n\n"
        "📱 <b>Hiddify</b> - Рекомендуемый клиент для подключения. <i>Возможны проблемы с подключением в мобильной сети.</i>\n\n"
        "📱 <b>V2Ray</b> - Альтернативный клиент для подключения. <i>Не отображает остаток трафика, но работает стабильнее.</i>\n"
    )

    await callback_query.message.edit_text(text, reply_markup=client_type_keyboard().as_markup(), parse_mode="HTML")


async def handle_download_app_hiddify(callback_query: CallbackQuery):
    """Скачивание приложения Hiddify."""
    text = (
        "Выберите платформу для загрузки:\n\n"
        "📱 <b>iOS</b> - Скачайте приложение для устройств Apple.\n"
        "🤖 <b>Android</b> - Скачайте приложение для Android устройств.\n"
        "💻 <b>Windows</b> - Скачайте приложение для Windows.\n"
        "🍏 <b>MacOS</b> - Скачайте приложение для MacOS.\n\n"
        "<i>🔽  Нажмите на нужную платформу для скачивания приложения.</i>"
    )
    await callback_query.message.edit_text(text, reply_markup=install_app_button_hiddify().as_markup(), parse_mode="HTML")


async def handle_download_app_v2ray(callback_query: CallbackQuery):
    """Скачивание приложения V2Ray."""
    text = (
        "Выберите платформу для загрузки:\n\n"
        "📱 <b>iOS</b> - Скачайте приложение для устройств Apple.\n"
        "🤖 <b>Android</b> - Скачайте приложение для Android устройств.\n"
        "💻 <b>Windows</b> - Скачайте приложение для Windows.\n"
        "🍏 <b>MacOS</b> - Скачайте приложение для MacOS.\n\n"
        "<i>🔽  Нажмите на нужную платформу для скачивания приложения.</i>"
    )
    await callback_query.message.edit_text(text, reply_markup=install_app_button_v2ray().as_markup(), parse_mode="HTML")


async def handle_reg_subscription(callback_query: CallbackQuery):
    """Выбор подписки."""
    text_parts = ["Выберите подписку:\n\n"]

    for tariff_key, tariff_info in config.TARIFFS.items():
        text_parts.append(f"<b>{tariff_info['emoji']} Подписка на {tariff_info['package_days']} дней:</b>\n")
        text_parts.append(f"💵 Сумма: {tariff_info['price']} рублей\n")
        text_parts.append(f"⏳ Доступ: {tariff_info['package_days']} дней\n")
        text_parts.append(f"🔒 Объем трафика: {tariff_info['usage_limit_GB']} Gb\n\n")

    text_parts.append("Выберите подходящий вариант и следуйте инструкциям для оплаты.")
    text = ''.join(text_parts)

    await callback_query.message.edit_text(text, reply_markup=subscription_buttons().as_markup(), parse_mode="HTML")


async def handle_add_balance(callback_query: CallbackQuery):
    """Выбор тарифа для пополнения."""
    data = callback_query.data
    if data.startswith("add_balance_"):
        tariff_key = data.split("_")[-1]
        tariff = config.TARIFFS.get(tariff_key)

        if tariff:
            # Сохраняем выбранный тариф в базу данных
            subscription_service.save_tariff_to_profile(callback_query.from_user.id, tariff)

            amount = tariff["price"]
            text = (
                "Пополнение баланса 💰\n\n"
                "📌 Для пополнения баланса используйте следующие данные:\n"
                f"💵 <b>Сумма:</b> {amount} рублей\n"
                "⏳ <b>Время на пополнение:</b> 60 минут\n\n"
                "<b>⚠ После оплаты отправьте чек в чат для подтверждения. <i>(скриншот или документ)</i></b>"
            )
            keyboard = confirm_payment_button(callback_query.from_user.id)
            await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
            await payment_service.notify_admin_about_payment(callback_query.from_user.id, amount)
        else:
            await callback_query.message.edit_text("Ошибка")


async def handle_confirm_payment(callback_query: CallbackQuery):
    """Подтверждение оплаты пользователем."""
    await notification_service.notify_payment_received(
        callback_query.message.chat.id,
        callback_query.from_user.id
    )
    
    keyboard = confirm_payment_button_done(callback_query.from_user.id)
    message_text = (
        "<b>Спасибо за подтверждение платежа! 😊</b>\n\n"
        "Ваш платеж будет обработан в ближайшее время. 🕒\n\n"
        "Для завершения процесса, пожалуйста, <b>пришлите скриншот подтверждения оплаты.</b> 📸\n\n"
        "Это поможет нам быстрее подтвердить ваш платеж и активировать услуги. Благодарим за понимание! 🙏"
    )
    await callback_query.message.edit_text(message_text, reply_markup=keyboard.as_markup(), parse_mode="HTML")


async def handle_admin_balance(callback_query: CallbackQuery):
    """Пополнение баланса админом."""
    parts = callback_query.data.split('_')
    if len(parts) != 4:
        await callback_query.answer("Ошибка в данных колбэка.")
        return

    target_user_id, amount = int(parts[2]), int(parts[3])
    payment_service.update_balance(target_user_id, amount)

    # Отправляем уведомление пользователю
    user_info = db.get_user(target_user_id)
    profile_data = json.loads(user_info[3]) if user_info and user_info[3] else {}
    balance = profile_data.get("balance", 0)
    
    user_message = (
        f"✅ Ваш баланс пополнен на <b>{amount}</b> рублей.\n\n"
        f"💰 <b>Текущий баланс:</b> {balance} руб.\n\n"
        f"Теперь вы можете оформить подписку."
    )
    keyboard = connect_buttons(target_user_id)
    await callback_query.message.bot.send_message(
        target_user_id,
        user_message,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    # Редактируем сообщение админа
    await callback_query.message.edit_text(
        f"💰 Баланс пользователя {target_user_id} пополнен на {amount} рублей.",
        reply_markup=None
    )


async def handle_cancel_payment(callback_query: CallbackQuery):
    """Отмена оплаты."""
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(
        "Баланс не пополнен. Операция отменена.",
        reply_markup=main_menu_buttons(user_id).as_markup()
    )


async def show_reset_traffic_confirmation(callback_query: CallbackQuery):
    """Показ подтверждения сброса трафика."""
    user_id = callback_query.from_user.id
    user_info = db.get_user(user_id)

    if not user_info:
        await callback_query.message.edit_text("⚠ Пользователь не найден.")
        return

    profile_data = json.loads(user_info[3])
    balance = profile_data.get("balance", 0)
    ticket_tariff = profile_data.get("ticket_tariff", {})
    charge_amount = ticket_tariff.get("price", 0)
    package_days = ticket_tariff.get("package_days", 0)

    text = (
        f"⚠️ <b>Подтверждение обновления подписки</b>\n\n"
        f"Вы уверены, что хотите обновить подписку?\n\n"
        f"💰 <b>Текущий баланс:</b> {balance} руб.\n"
        f"💸 <b>Будет списано:</b> {charge_amount} руб.\n"
        f"📅 <b>Продление на:</b> {package_days} дней\n"
        f"💵 <b>Остаток после списания:</b> {balance - charge_amount} руб.\n\n"
        f"После подтверждения ваш трафик будет сброшен и подписка продлена."
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, обновить", callback_data="confirm_reset_traffic")
    builder.button(text="❌ Отмена", callback_data="cancel_reset_traffic")
    builder.adjust(2)

    await callback_query.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


async def handle_confirm_reset_traffic(callback_query: CallbackQuery):
    """Подтверждение сброса трафика."""
    user_id = callback_query.from_user.id
    result = await subscription_service.reset_traffic(user_id)

    if "error" in result:
        await callback_query.message.edit_text(f"❌ {result['error']}")
        return

    if result.get("message") == "Сброс не требуется":
        text = "Сброс трафика не требуется."
    else:
        text = (
            f"✅ <b>Подписка успешно обновлена!</b>\n\n"
            f"💸 Списано: {result['charge_amount']} руб.\n"
            f"💰 Остаток баланса: {result['new_balance']} руб.\n"
            f"📅 Подписка продлена на {result['package_days']} дней\n"
            f"📊 Трафик сброшен\n\n"
            f"Можете продолжать пользоваться сервисом!"
        )

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В главное меню", callback_data="main_menu")
    await callback_query.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


async def handle_get_users(callback_query: CallbackQuery):
    """Получение списка пользователей (админ)."""
    from aiogram.types import Message
    import html as html_module
    
    user_id = callback_query.from_user.id
    
    if not config.is_admin(user_id):
        await callback_query.message.answer("⛔ У вас нет прав для просмотра списка пользователей.")
        return
    
    try:
        users_info = hiddify_service.get_users_list()
        
        if isinstance(users_info, list):
            users_list = "\n\n".join(users_info)
        else:
            users_list = users_info

        # Разбиваем текст на части, если он слишком длинный
        max_length = 3000
        if len(users_list) > max_length:
            parts = [users_list[i:i + max_length] for i in range(0, len(users_list), max_length)]
            for i, part in enumerate(parts):
                part = html_module.escape(part)
                header = f"📜 <b>Список пользователей (часть {i + 1} из {len(parts)}):</b>\n\n"
                await callback_query.message.answer(
                    header + part,
                    reply_markup=main_menu_back().as_markup() if i == len(parts) - 1 else None,
                    parse_mode="HTML"
                )
        else:
            users_list = html_module.escape(users_list)
            await callback_query.message.edit_text(
                f"📜 <b>Список пользователей:</b>\n\n{users_list}",
                reply_markup=main_menu_back().as_markup(),
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        await callback_query.message.answer("⚠️ Произошла ошибка при получении списка пользователей. Попробуйте позже.")


async def handle_user_connection(message: Message, user_id: int):
    """Обработка подключения пользователя."""
    user_info = db.get_user(user_id)
    if user_info is None:
        logger.error(f"Пользователь с user_id {user_id} не найден в базе данных.")
        await message.answer("⚠ Пользователь не найден. Используйте команду /start для регистрации.")
        return

    profile_data = user_info[3]
    profile = json.loads(profile_data)
    username = profile.get("username", "Unknown")
    profile_name = f"{username}-{user_id}"

    uuid = user_info[2]
    if not uuid or uuid == "N/A":
        tariff = profile.get("ticket_tariff", {"package_days": 30, "usage_limit_GB": 75})
        package_days = tariff["package_days"]
        usage_limit_GB = tariff["usage_limit_GB"]

        # Регистрируем в Hiddify (списание произойдёт внутри сервиса)
        result = await subscription_service.create_subscription(
            user_id=user_id,
            username=username,
            package_days=package_days,
            usage_limit_GB=usage_limit_GB,
            service_cost=payment_service.calculate_service_cost(package_days)
        )

        if "error" in result:
            await message.answer(f"Ошибка при регистрации: {result['error']}", reply_markup=main_menu_back().as_markup())
        else:
            await message.answer(
                f"✅ Подписка успешно создана! UUID: {result['uuid']}\n\n"
                f"📅 Срок подписки: {result['package_days']} дней\n"
                f"💰 Остаток баланса: {result['new_balance']} руб.\n\n"
                f"Теперь вы можете подключиться к сервису.",
                reply_markup=main_menu_back().as_markup()
            )
        return

    # Если UUID уже есть, показываем информацию
    api_user_info = hiddify_service.get_user_info(uuid)
    if api_user_info:
        # Форматируем ответ
        text = UserService.get_user_info_text(user_id, hiddify_service)
        await message.edit_text(text, reply_markup=main_menu_back().as_markup(), parse_mode="HTML")
