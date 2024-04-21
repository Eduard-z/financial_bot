from aiogram import types, F, Router
from aiogram.types import Message
from aiogram.filters import Command

import kb
import text

import expenses
import exceptions
from categories import Categories


router = Router()


@router.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        text.greet.format(name=message.from_user.full_name),
        reply_markup=kb.menu
    )


@router.message(F.text == "Меню")
async def menu(msg: Message):
    await msg.answer(text.menu, reply_markup=kb.menu)


@router.message(Command("help"))
async def menu_handler(message: types.Message):
    await message.answer(
        "Бот для учёта финансов\n\n"
        "Добавить расход: 25 такси\n"
        "Удалить расход: -25 такси\n"
        "Сегодняшняя статистика: /today\n"
        "За текущий месяц: /month\n"
        "Последние внесённые расходы: /expenses\n"
        "Категории трат: /categories"
    )


@router.message(Command("categories"))
async def categories_list(message: types.Message):
    """Отправляет список категорий расходов"""
    categories = Categories().get_all_categories()
    answer_message = "Категории трат:\n\n* " +\
        ("\n* ".join([c.name+' ('+", ".join(c.aliases)+')' for c in categories]))
    await message.answer(answer_message)


@router.message(Command("today"))
async def today_statistics(message: types.Message):
    """Отправляет сегодняшнюю статистику трат"""
    answer_message = expenses.get_today_statistics()
    await message.answer(answer_message)


@router.message(Command("month"))
async def month_statistics(message: types.Message):
    """Отправляет статистику трат текущего месяца"""
    answer_message = expenses.get_month_statistics()
    await message.answer(answer_message)


@router.message(Command("expenses"))
async def list_expenses(message: types.Message):
    """Отправляет последние несколько записей о расходах"""
    last_expenses = expenses.last()
    if not last_expenses:
        await message.answer("Расходы ещё не заведены")
        return

    last_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name}"
        for expense in last_expenses]
    answer_message = "Последние сохранённые траты:\n\n* " + "\n\n* "\
        .join(last_expenses_rows)
    await message.answer(answer_message)


@router.message(Command("id"))
async def message_handler(msg: Message):
    await msg.answer(f"Твой ID: {msg.from_user.id}")


@router.message(F.text.lower().__eq__("хуй"))
async def hui_special(message: types.Message):
    """Ответ на сообщение"""
    await message.answer("тебе")


@router.message(F.text.startswith("-"))
async def del_expense(message: types.Message):
    """Удаляет одну запись о расходе по её сумме и категории"""
    try:
        expense = expenses.delete_expense(message.text)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f"Удалены траты {expense.amount} руб на {expense.category_name}.\n\n"
        f"{expenses.get_today_statistics()}")
    await message.answer(answer_message)


@router.message()
async def add_expense(message: types.Message):
    """Добавляет новый расход"""
    try:
        expense = expenses.add_expense(message.text, message.from_user.id)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f"Добавлены траты {expense.amount} руб на {expense.category_name}.\n\n"
        f"{expenses.get_today_statistics()}")
    await message.answer(answer_message)
