"""Клавиатура главного меню."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BUTTON_ORDERS = "📋 Заказы"
BUTTON_WORKSHOP = "🏭 Мастерская"
BUTTON_PROFILE = "👤 Профиль"
BUTTON_HELP = "❓ Помощь"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Постоянная клавиатура главного меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_ORDERS), KeyboardButton(text=BUTTON_WORKSHOP)],
            [KeyboardButton(text=BUTTON_PROFILE), KeyboardButton(text=BUTTON_HELP)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери действие в меню",
    )
