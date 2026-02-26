"""
Клавиатуры для профиля пользователя.
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder


def profile_type_keyboard() -> InlineKeyboardBuilder:
    """
    Выбор типа профиля (Hiddify или V2Ray).
    
    Returns:
        InlineKeyboardBuilder с кнопками выбора типа
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Hiddify профиль", callback_data="link_hiddify")
    builder.button(text="📱 V2Ray профиль", callback_data="link_v2ray")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder


def install_app_button_hiddify() -> InlineKeyboardBuilder:
    """
    Кнопки для скачивания приложения Hiddify.
    
    Returns:
        InlineKeyboardBuilder с кнопками платформ
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 iOS", url="https://apps.apple.com/us/app/hiddify-proxy-vpn/id6596777532?platform=iphone")
    builder.button(text="🤖 Android", url="https://play.google.com/store/apps/details?id=app.hiddify.com")
    builder.button(text="💻 Windows", url="https://apps.microsoft.com/detail/9pdfnl3qv2s5?hl=ru-RU&gl=RU")
    builder.button(text="🍏 MacOS", url="https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-MacOS.dmg")
    builder.button(text="◀️ Назад", callback_data="download_app")
    builder.adjust(2, 2, 1)
    return builder


def install_app_button_v2ray() -> InlineKeyboardBuilder:
    """
    Кнопки для скачивания приложения V2Ray.
    
    Returns:
        InlineKeyboardBuilder с кнопками платформ
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 iOS", url="https://apps.apple.com/en/app/v2raytun/id6476628951")
    builder.button(text="🤖 Android", url="https://play.google.com/store/apps/details?id=com.v2raytun.android")
    builder.button(text="💻 Windows", url="https://apps.microsoft.com/detail/9pdfnl3qv2s5?hl=ru-RU&gl=RU")
    builder.button(text="🍏 MacOS", url="https://apps.apple.com/en/app/v2raytun/id6476628951")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(2, 2, 1)
    return builder


def client_type_keyboard() -> InlineKeyboardBuilder:
    """
    Выбор клиента (Hiddify или V2Ray).
    
    Returns:
        InlineKeyboardBuilder с кнопками выбора
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Hiddify", callback_data="download_app_hiddify")
    builder.button(text="📱 V2Ray", callback_data="download_app_v2ray")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder
