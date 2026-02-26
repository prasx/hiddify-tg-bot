"""
Клавиатуры для Telegram бота.
"""

from .main_menu import main_menu_buttons, main_menu_back, connect_buttons, balance_keyboard
from .subscription import subscription_buttons, subscription_action_buttons
from .payment import confirm_payment_button, confirm_payment_button_done, admin_payment_buttons
from .profile import profile_type_keyboard, install_app_button_hiddify, install_app_button_v2ray, client_type_keyboard
from .admin import admin_payment_confirm_buttons, admin_payment_done_buttons

__all__ = [
    "main_menu_buttons",
    "main_menu_back",
    "connect_buttons",
    "balance_keyboard",
    "subscription_buttons",
    "subscription_action_buttons",
    "confirm_payment_button",
    "confirm_payment_button_done",
    "admin_payment_buttons",
    "profile_type_keyboard",
    "install_app_button_hiddify",
    "install_app_button_v2ray",
    "client_type_keyboard",
    "admin_payment_confirm_buttons",
    "admin_payment_done_buttons",
]
