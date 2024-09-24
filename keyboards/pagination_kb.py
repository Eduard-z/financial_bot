from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lexicon import LEXICON_RU


# Функция, генерирующая клавиатуру
def create_pagination_keyboard(*buttons: str) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    # Добавляем в билдер ряд с кнопками,
    # если ключа в словаре нет, то текст остается таким же, каким был передан в функцию
    kb_builder.row(*[
        InlineKeyboardButton(
            text=LEXICON_RU[button] if button in LEXICON_RU else button,
            callback_data=button
        ) for button in buttons
    ])
    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()
