from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
menu = [
    [InlineKeyboardButton(text="💰 Баланс за сегодня", callback_data="/today"),
     InlineKeyboardButton(text="💰 Баланс за месяц", callback_data="month_statistics")],
    [InlineKeyboardButton(text="Мой айди", callback_data="id"),
     InlineKeyboardButton(text="🔎 Помощь", callback_data="/help")],
]
menu = InlineKeyboardMarkup(inline_keyboard=menu)
exit_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="◀️ Выйти в меню")]], resize_keyboard=True)
iexit_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Выйти в меню", callback_data="menu")]])
