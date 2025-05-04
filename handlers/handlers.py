from aiogram import types, F, Router
from aiogram.types import Message, CallbackQuery, ErrorEvent, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from middlewares import AllowUsersOnlyMiddleware
from keyboards import keyboard, create_pagination_keyboard
from lexicon import LEXICON_RU
from filters import (IsDigitCallbackData, IsExpenseFilter,
                     IsDeleteExpenseFilter, IsTelegramIdFilter)
from states import FSMAddFamilyAccount
from exceptions import NotCorrectMessage
from models import expenses, Categories, family_accounts

router = Router()
router.message.middleware(AllowUsersOnlyMiddleware())
router.callback_query.middleware(AllowUsersOnlyMiddleware())


@router.error()
async def error_handler(event: ErrorEvent, _logger):
    _logger.critical("Critical error caused by %s", event.exception, exc_info=True)
    _logger.critical(event.update)


@router.message(F.text == "Меню")
async def menu_handler(message: Message, _logger):
    _logger.info("User asked to display the Menu")
    await message.answer(text=LEXICON_RU["menu"], reply_markup=keyboard)


@router.message(Command(commands="help"))
@router.message(F.text == LEXICON_RU["help"])
async def help_menu_handler(message: types.Message, _logger):
    _logger.info("User asked for help")
    await message.answer(
        "Бот для учёта финансов\n\n"
        "Добавить расход: 12.5 такси\n"
        "Удалить расход: -12.5 такси\n"
        "Статистика за текущий месяц: /month\n"
        "Последние внесённые расходы: /expenses\n"
        "Категории трат: /categories\n"
        "Добавить семейный аккаунт: /family\n"
        "Для вызова меню напишите 'Меню'",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("categories"))
@router.message(F.text == LEXICON_RU["categories"])
async def categories_list(message: types.Message, _logger):
    """Отправляет список категорий расходов"""
    _logger.info("User asked for categories list")
    categories = Categories().get_all_categories()
    _logger.debug(f"Categories list: {categories}")

    def is_basic(is_base: bool):
        """ Indicates base expenses (not used) """
        if is_base:
            return "[баз.]"
        else:
            return ""

    answer_message = "Категории трат:\n\n* " +\
        ("\n* ".join(
            [c.name + ' ' + '(' + ", ".join(c.aliases) + ')' for c in categories]
        ))
    await message.answer(text=answer_message, reply_markup=keyboard)


@router.message(Command("today"))
@router.message(F.text == LEXICON_RU["balance_today"])
async def today_statistics(message: types.Message, _logger):
    """Отправляет сегодняшнюю статистику трат"""
    _logger.info("User asked for today expenses list")
    answer_message = expenses.get_today_statistics(message.from_user.id)
    await message.answer(text=answer_message, reply_markup=keyboard)


@router.message(Command("month"))
@router.message(F.text == LEXICON_RU["balance_month"])
@router.message(F.text == LEXICON_RU["balance_past_month"])
async def month_statistics(message: types.Message, _logger):
    show_rows = 5
    if message.text in (LEXICON_RU["balance_month"], "/month"):
        """Отправляет статистику трат текущего месяца"""
        _logger.info("User asked for current month expenses list")
        month = "current_month"
    elif message.text == LEXICON_RU["balance_past_month"]:
        """Отправляет статистику трат прошлого месяца"""
        _logger.info("User asked for past month expenses list")
        month = "past_month"
    else:
        raise Exception("Wrong command for month statistics")

    month_expenses = _get_month_expenses(message.from_user.id, month, _logger)
    if not month_expenses:
        await message.answer("Расходы ещё не заведены")
        return

    expenses_rows_total = len(month_expenses)
    _logger.debug(f"Month expenses total rows: {expenses_rows_total}")

    all_month_expenses = sum([expense.amount for expense in month_expenses])
    _logger.debug(f"Month expenses sum: {all_month_expenses}")

    month_expenses_per_page = _get_month_expenses_per_page(month_expenses, show_rows, 0, _logger)
    account_type = _get_account_type(message.from_user.id, month_expenses, _logger)

    answer_message = "Траты за месяц "\
        f"({account_type}):\nВсего - {all_month_expenses}\n\n* " + "\n\n* "\
        .join(month_expenses_per_page)

    if expenses_rows_total > show_rows:
        _logger.info(f"Expenses: in case total rows {expenses_rows_total} > {show_rows}")
        await message.answer(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                '1',
                f'forward_{month}'
            )
        )
    elif expenses_rows_total <= show_rows:
        _logger.info(f"Expenses: in case total rows {expenses_rows_total} <= {show_rows}")
        await message.answer(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                '1',
            )
        )


@router.message(Command("expenses"))
@router.message(F.text == LEXICON_RU["last_expenses"])
async def list_expenses(message: types.Message, _logger):
    """Отправляет последние несколько записей о расходах"""
    _logger.info("User asked for last expenses list")
    last_expenses = expenses.last(message.from_user.id)
    _logger.debug(f"Last expenses: {last_expenses}")

    if not last_expenses:
        await message.answer("Расходы ещё не заведены")
        return

    last_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name} — нажми "
        f"/del{expense.id} для удаления"
        for expense in last_expenses
    ]
    answer_message = "Последние сохранённые траты:\n\n* " + "\n\n* "\
        .join(last_expenses_rows)
    await message.answer(answer_message)


@router.message(F.text, IsExpenseFilter())
async def add_expense(message: types.Message, _logger, amount, product):
    """Добавляет новый расход"""
    _logger.info(f"User asked to add an expense: {amount} for {product}")
    try:
        expense = expenses.add_expense(amount, product, message.text, message.from_user.id)
        if not expense:
            _logger.error(f"Expense {expense} has NOT been added")
        _logger.info(f"{expense} has been added")
    except NotCorrectMessage as e:
        _logger.exception(e)
        await message.answer(e.message)
        return
    answer_message = (
        f"Добавлены траты {expense.amount} руб на {expense.category_name}.\n\n"
        f"{expenses.get_today_statistics(message.from_user.id)}"
    )
    await message.answer(text=answer_message, reply_markup=keyboard)


@router.message(F.text, IsDeleteExpenseFilter())
async def del_expense(message: types.Message, _logger, amount, product):
    """Удаляет одну запись о расходе по её сумме и категории"""
    _logger.info(f"User asked to delete an expense: {amount} for {product}")
    try:
        expense = expenses.delete_expense(amount, product, message.from_user.id)
        if not expense:
            _logger.error(f"Expense {expense} has NOT been deleted")
        _logger.info(f"Trying to delete {amount} for {product}")
    except Exception as e:
        _logger.exception(e)
        await message.answer(str(e))
        return
    if expense:
        answer_message = (
            f"Удалены траты {expense.amount} руб на {expense.category_name}.\n\n"
            f"{expenses.get_today_statistics(message.from_user.id)}"
        )
    else:
        answer_message = "Ошибка: такого расхода не существует"
        _logger.info(f"Unable to delete: {amount} for {product} does not exist")
    await message.answer(text=answer_message, reply_markup=keyboard)


@router.message(F.text, lambda message: message.text.startswith('/del'))
async def del_expense_by_id(message: Message, _logger):
    """Удаляет одну запись о расходе по её идентификатору"""
    _logger.info("User asked to delete an expense by id")
    row_id = message.text[4:]
    try:
        row_id = int(row_id)
    except ValueError as e:
        _logger.exception(e)
        _logger.info(message.model_dump_json(indent=4, exclude_none=True))
        await message.answer(text="Impossible to identify the expense by id")
        return
    else:
        answer_message = expenses.delete_expense_by_id(row_id)
        _logger.info(answer_message)
    await message.answer(answer_message)


# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки "вперед"
# во время взаимодействия пользователя с месячной статистикой
@router.callback_query(F.data.in_({"forward_current_month", "forward_past_month"}))
async def process_forward_press(callback: CallbackQuery, _logger):
    button_pressed = callback.data
    button_pressed_postfix = callback.data.lstrip("forward_")
    _logger.info(f"User pressed {button_pressed}")

    month_expenses = _get_month_expenses(callback.from_user.id, button_pressed_postfix, _logger)
    if not month_expenses:
        await callback.message.edit_text(text="Расходы ещё не заведены",)
        return

    show_rows = 5
    pages_total = len(month_expenses) / show_rows
    _logger.debug(f"Month expenses total pages: {pages_total}")

    rows_remainder = len(month_expenses) % show_rows
    _logger.debug(f"Month expenses last page remainder: {rows_remainder}")

    current_page = int(list(filter(
        lambda x: x.isdigit(), [
            i.text for i in callback.message.reply_markup.inline_keyboard[0]
        ]
    ))[0])

    month_expenses_per_page = _get_month_expenses_per_page(
        month_expenses,
        show_rows,
        0 + show_rows * current_page,
        _logger
    )
    account_type = _get_account_type(callback.from_user.id, month_expenses, _logger)

    answer_message = "Траты за месяц "\
        f"({account_type}):\n\n* " + "\n\n* "\
        .join(month_expenses_per_page)

    if pages_total > (current_page + 1):
        _logger.info(f"Expenses: in case total pages {pages_total} > {current_page} + 1")
        await callback.message.edit_text(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                f'backward_{button_pressed_postfix}',
                f'{current_page + 1}',
                f'forward_{button_pressed_postfix}'
            )
        )
    elif pages_total > current_page:
        _logger.info(f"Expenses: in case total pages {pages_total} > {current_page}")
        await callback.message.edit_text(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                f'backward_{button_pressed_postfix}',
                f'{current_page + 1}',
            )
        )
    else:
        await callback.answer()
        _logger.info(callback.model_dump_json(indent=4, exclude_none=True))
        _logger.exception("Текущая страница больше общего количества страниц")


# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки "назад"
# во время взаимодействия пользователя с месячной статистикой
@router.callback_query(F.data.in_({"backward_current_month", "backward_past_month"}))
async def process_backward_press(callback: CallbackQuery, _logger):
    button_pressed = callback.data
    button_pressed_postfix = callback.data.lstrip("backward").lstrip("_")
    _logger.info(f"User pressed {button_pressed}")

    month_expenses = _get_month_expenses(callback.from_user.id, button_pressed_postfix, _logger)
    if not month_expenses:
        await callback.message.edit_text(text="Расходы ещё не заведены",)
        return

    show_rows = 5
    current_page = int(callback.message.reply_markup.inline_keyboard[0][1].text)

    month_expenses_per_page = _get_month_expenses_per_page(
        month_expenses,
        show_rows,
        0 + show_rows * (current_page - 2),
        _logger
    )
    account_type = _get_account_type(callback.from_user.id, month_expenses, _logger)

    answer_message = "Траты за месяц "\
        f"({account_type}):\n\n* " + "\n\n* "\
        .join(month_expenses_per_page)

    if current_page > 2:
        _logger.info(f"Expenses: in case current page {current_page} > 2")
        await callback.message.edit_text(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                f'backward_{button_pressed_postfix}',
                f'{current_page - 1}',
                f'forward_{button_pressed_postfix}'
            )
        )
    elif current_page > 1:
        _logger.info(f"Expenses: in case current page {current_page} > 1")
        await callback.message.edit_text(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                f'{current_page - 1}',
                f'forward_{button_pressed_postfix}'
            )
        )
    else:
        await callback.answer()
        _logger.info(callback.model_dump_json(indent=4, exclude_none=True))
        _logger.exception("Текущая страница 1")


# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# с номером текущей страницы
@router.callback_query(IsDigitCallbackData())
async def process_page_press(callback: CallbackQuery, _logger):
    _logger.info("User pressed page number")
    await callback.answer()


# Этот хэндлер будет срабатывать на команду /family
# и переводить бота в состояние ожидания ввода telegram ID
@router.message(Command("family"), StateFilter(default_state))
@router.message(F.text == LEXICON_RU["family"], StateFilter(default_state))
async def process_add_family_command(message: types.Message, state: FSMContext, _logger):
    _logger.info("User asked to add their family telegram ID")
    _logger.debug(f"User being in state '{await state.get_state()}'")

    family_accounts_list = family_accounts.get_family_accounts(message.from_user.id)
    _logger.debug(f"Linked family accounts: {family_accounts_list}")
    if not family_accounts_list:
        answer_message = "Семейные аккаунты не привязаны"\
            "\n\nКакой telegram ID привязать?"
    elif family_accounts_list:
        family_accounts_rows = [
            f"{account.family_id} — нажми /unlink{account.id} для удаления"
            for account in family_accounts_list
        ]

        answer_message = "Привязанные семейные аккаунты:\n\n* " + "\n\n* "\
            .join(family_accounts_rows) + "\n\nКакой telegram ID привязать?"
    else:
        _logger.debug(message.model_dump_json(indent=4, exclude_none=True))
        raise Exception(f"Invalid family accounts list {family_accounts_list}")

    await message.answer(
        text=answer_message,
        reply_markup=ReplyKeyboardRemove()
    )
    # Устанавливаем состояние ожидания ввода telegram ID
    await state.set_state(FSMAddFamilyAccount.fill_family_account)


@router.message(F.text, lambda message: message.text.startswith('/unlink'))
async def del_family_account_by_id(message: Message, state: FSMContext, _logger):
    """Удаляет семейный аккаунт по его идентификатору"""
    _logger.info("User asked to delete family account by id")
    _logger.debug(f"User being in state '{await state.get_state()}'")
    account_id = message.text[7:]
    try:
        account_id = int(account_id)
    except ValueError as e:
        _logger.exception(e)
        _logger.info(message.model_dump_json(indent=4, exclude_none=True))
        await message.answer(text="Impossible to identify the account by id")
        return
    else:
        answer_message = family_accounts\
            .delete_family_account_by_id(account_id, message.from_user.id)
        _logger.info(answer_message)
    await message.answer(
        text=answer_message,
        reply_markup=keyboard
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


# Этот хэндлер будет срабатывать, если бот находится в состоянии ожидания
# ввода telegram ID, но сам ID некорректный, и отключать машину состояний
@router.message(StateFilter(FSMAddFamilyAccount.fill_family_account), ~IsTelegramIdFilter())
async def process_wrong_telegram_id(message: types.Message, state: FSMContext, _logger):
    _logger.info(f"User {message.from_user.id} entered wrong telegram ID {message.text}")
    _logger.debug(f"User being in state '{await state.get_state()}'")
    await message.answer(
        text="Вы ввели некорректный telegram ID\n\n"
             "Чтобы снова отправить telegram ID - "
             "нажмите 'Привязать семейный аккаунт'",
        reply_markup=keyboard
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


# Этот хэндлер будет срабатывать, если корректно введён telegram ID,
# и отключать машину состояний
@router.message(StateFilter(FSMAddFamilyAccount.fill_family_account), IsTelegramIdFilter())
async def process_telegram_id_sent(message: types.Message, state: FSMContext, _logger):
    _logger.info(f"User {message.from_user.id} entered family telegram ID {message.text}")
    _logger.debug(f"User being in state '{await state.get_state()}'")
    # Сохраняем введённый telegram ID в хранилище
    try:
        family_account = family_accounts.link_family_accounts(message.from_user.id, message.text)
        _logger.info(f"{family_account} has been added")
    except NotCorrectMessage as e:
        _logger.exception(e)
        await message.answer(str(e))
        return
    await message.answer(
        text=f"telegram ID {family_account.family_id} добавлен",
        reply_markup=keyboard
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


@router.message(F.text.lower().__eq__("хуй"))
async def hui_special(message: types.Message, _logger):
    """Ответ на сообщение"""
    _logger.info("User typed hui")
    await message.answer("тебе")


@router.message(F.text.lower().__eq__("пизда"))
async def pizda_special(message: types.Message, _logger):
    """Ответ на сообщение"""
    _logger.info("User typed pizda")
    await message.answer("рулю")


# Этот хэндлер будет реагировать на сообщения типа "не текст"
@router.message(~F.text)
async def not_text_handler(message: types.Message, _logger):
    _logger.info(
        f"User sent not text: {message.model_dump_json(indent=4, exclude_none=True)}"
    )
    await message.answer("Я понимаю только текст!")


# Этот хэндлер будет реагировать на любые сообщения пользователя,
# не предусмотренные логикой работы бота
@router.message()
async def send_echo(message: types.Message, _logger):
    _logger.info(f"User typed an incorrect command: {message.text}")
    _logger.debug(message.model_dump_json(indent=4, exclude_none=True))
    await message.answer(f"Это эхо! {message.text}")


def _get_month_expenses(user_id: int, month: str, _logger) -> list[expenses.Expense]:
    month_expenses = expenses.get_month_statistics(user_id, month)
    _logger.debug(f"{month} expenses: {month_expenses}")
    return month_expenses


def _get_month_expenses_per_page(month_expenses: list[expenses.Expense],
                                 limit: int, offset: int, _logger) -> list[str]:
    month_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name}"
        for expense in month_expenses]

    return month_expenses_rows[offset:(limit + offset)]


def _get_account_type(user_id: int, month_expenses: list[expenses.Expense], _logger) -> str:
    if month_expenses[0].user_id == user_id:
        account_type = "личный аккаунт"
    elif month_expenses[0].user_id != user_id:
        account_type = "семейный аккаунт"
    else:
        raise Exception(f"Wrong account #{user_id} type")

    _logger.debug(f"Account type: {account_type} ({month_expenses[0].user_id} vs {user_id})")
    return account_type
