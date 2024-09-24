from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from lexicon import LEXICON_RU


balance_today_button = KeyboardButton(text=LEXICON_RU["balance_today"])
balance_month_button = KeyboardButton(text=LEXICON_RU["balance_month"])
balance_past_month_button = KeyboardButton(text=LEXICON_RU["balance_past_month"])
categories_button = KeyboardButton(text=LEXICON_RU["categories"])
last_expenses_button = KeyboardButton(text=LEXICON_RU["last_expenses"])
my_id_button = KeyboardButton(text=LEXICON_RU["my_id"])
help_button = KeyboardButton(text=LEXICON_RU["help"])

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [balance_month_button, balance_past_month_button],
        [last_expenses_button, categories_button]
    ],
    resize_keyboard=True
)
