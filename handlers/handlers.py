from aiogram import types, F, Router
from aiogram.types import Message, CallbackQuery, ErrorEvent, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from middlewares import AllowAdminsOnlyMiddleware
from keyboards import keyboard, create_pagination_keyboard
from lexicon import LEXICON_RU
from filters import (IsDigitCallbackData, IsExpenseFilter,
                     IsDeleteExpenseFilter, IsTelegramIdFilter)
from states import FSMAddFamilyAccount
from exceptions import NotCorrectMessage
from models import expenses, Categories, family_accounts

router = Router()
router.message.middleware(AllowAdminsOnlyMiddleware())
router.callback_query.middleware(AllowAdminsOnlyMiddleware())


@router.error()
async def error_handler(event: ErrorEvent, _logger):
    _logger.critical("Critical error caused by %s", event.exception, exc_info=True)
    _logger.critical(event.update)


@router.message(F.text == "Меню")
async def menu_handler(message: Message, _logger):
    _logger.info("User asked to display the Menu")
    await message.answer(text=LEXICON_RU["menu"], reply_markup=keyboard)


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
    if message.text in (LEXICON_RU["balance_month"], "/month"):
        """Отправляет статистику трат текущего месяца"""
        _logger.info("User asked for current month expenses list")
        month = "current_month"
        month_expenses = expenses.get_month_statistics(message.from_user.id)
        _logger.debug(f"Month expenses: {month_expenses}")
    elif message.text == LEXICON_RU["balance_past_month"]:
        """Отправляет статистику трат прошлого месяца"""
        _logger.info("User asked for past month expenses list")
        month = "past_month"
        month_expenses = expenses.get_past_month_statistics(message.from_user.id)
        _logger.debug(f"Past month expenses: {month_expenses}")
    else:
        raise Exception("Wrong command for month statistics")

    if not month_expenses:
        await message.answer("Расходы ещё не заведены")
        return

    month_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name}"
        for expense in month_expenses]

    show_rows = 5
    expenses_rows_total = len(month_expenses_rows)
    _logger.debug(f"Month expenses total rows: {expenses_rows_total}")

    all_month_expenses = sum([expense.amount for expense in month_expenses])
    _logger.debug(f"Month expenses sum: {all_month_expenses}")

    if month_expenses[0].user_id in (message.from_user.id, "("):
        account_type = "личный аккаунт"
    elif month_expenses[0].user_id not in (message.from_user.id, "("):
        account_type = "семейный аккаунт"
    else:
        raise Exception(f"Wrong account #{message.from_user.id} type")

    answer_message = "Траты за месяц "\
        f"({account_type}):\nВсего - {all_month_expenses}\n\n* " + "\n\n* "\
        .join(month_expenses_rows[0:show_rows])

    if expenses_rows_total > show_rows:
        await message.answer(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                '1',
                f'forward_{month}'
            )
        )
    elif expenses_rows_total <= show_rows:
        show_rows = expenses_rows_total

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
        _logger.info(f"{expense} has been added")
    except NotCorrectMessage as e:
        _logger.exception(e)
        await message.answer(e)
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
        _logger.info(f"{expense} has been deleted")
    except Exception as e:
        _logger.exception(e)
        await message.answer(e)
        return
    if expense:
        answer_message = (
            f"Удалены траты {expense.amount} руб на {expense.category_name}.\n\n"
            f"{expenses.get_today_statistics(message.from_user.id)}"
        )
    else:
        answer_message = "Expense does not exist"
        _logger.info("Expense does not exist")
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
        await message.answer(text="Impossible to identify the expense")
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
    button_pressed_postfix = callback.data.lstrip("forward")

    _logger.info(f"User pressed {button_pressed}")

    if button_pressed == "forward_current_month":
        month_expenses = expenses.get_month_statistics(callback.from_user.id)
    elif button_pressed == "forward_past_month":
        month_expenses = expenses.get_past_month_statistics(callback.from_user.id)
    else:
        await callback.answer()
        _logger.info(callback.model_dump_json(indent=4, exclude_none=True))
        _logger.exception("Wrong button received")
    _logger.debug(f"Month expenses: {month_expenses}")

    if not month_expenses:
        await callback.message.edit_text(text="Расходы ещё не заведены",)
        return

    month_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name}"
        for expense in month_expenses]

    show_rows = 5
    pages_total = len(month_expenses_rows) / show_rows
    rows_remainder = len(month_expenses_rows) % show_rows
    current_page = int(list(filter(
        lambda x: x.isdigit(), [
            i.text for i in callback.message.reply_markup.inline_keyboard[0]
        ]
    ))[0])

    if month_expenses[0].user_id in (callback.from_user.id, "("):
        account_type = "личный аккаунт"
    elif month_expenses[0].user_id not in (callback.from_user.id, "("):
        account_type = "семейный аккаунт"
    else:
        raise Exception(f"Wrong account #{callback.from_user.id} type")

    answer_message = "Траты за месяц "\
        f"({account_type}):\n\n* " + "\n\n* "\
        .join(month_expenses_rows[
            0 + show_rows * current_page:show_rows + show_rows * current_page
        ])

    if pages_total > (current_page + 1):
        _logger.info(f"if {pages_total} > {current_page} + 1")
        await callback.message.edit_text(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                f'backward{button_pressed_postfix}',
                f'{current_page + 1}',
                f'forward{button_pressed_postfix}'
            )
        )
    elif pages_total > current_page:
        _logger.info(f"if {pages_total} > {current_page}")

        if rows_remainder:
            show_rows = rows_remainder
        await callback.message.edit_text(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                f'backward{button_pressed_postfix}',
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
    button_pressed_postfix = callback.data.lstrip("backward")

    _logger.info(f"User pressed {button_pressed}")

    if button_pressed == "backward_current_month":
        month_expenses = expenses.get_month_statistics(callback.from_user.id)
    elif button_pressed == "backward_past_month":
        month_expenses = expenses.get_past_month_statistics(callback.from_user.id)
    else:
        await callback.answer()
        _logger.info(callback.model_dump_json(indent=4, exclude_none=True))
        _logger.exception("Wrong button received")
    _logger.debug(f"Month expenses: {month_expenses}")

    if not month_expenses:
        await callback.message.edit_text(text="Расходы ещё не заведены",)
        return

    month_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name}"
        for expense in month_expenses]

    show_rows = 5
    current_page = int(callback.message.reply_markup.inline_keyboard[0][1].text)

    if month_expenses[0].user_id in (callback.from_user.id, "("):
        account_type = "личный аккаунт"
    elif month_expenses[0].user_id not in (callback.from_user.id, "("):
        account_type = "семейный аккаунт"
    else:
        raise Exception(f"Wrong account #{callback.from_user.id} type")

    answer_message = "Траты за месяц "\
        f"({account_type}):\n\n* " + "\n\n* "\
        .join(month_expenses_rows[
            0 + show_rows * (current_page - 2):show_rows + show_rows * (current_page - 2)
        ])

    if current_page > 2:
        _logger.info(f"if {current_page} > 2")
        await callback.message.edit_text(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                f'backward{button_pressed_postfix}',
                f'{current_page - 1}',
                f'forward{button_pressed_postfix}'
            )
        )
    elif current_page > 1:
        _logger.info(f"if {current_page} > 1")
        await callback.message.edit_text(
            text=answer_message,
            reply_markup=create_pagination_keyboard(
                f'{current_page - 1}',
                f'forward{button_pressed_postfix}'
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


@router.message(
    StateFilter(FSMAddFamilyAccount.fill_family_account),
    F.text,
    lambda message: message.text.startswith('/unlink')
)
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
        await message.answer(text="Impossible to identify the account")
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
    # Cохраняем введённый telegram ID в хранилище
    try:
        family_account = family_accounts.link_family_accounts(message.from_user.id, message.text)
        _logger.info(f"{family_account} has been added")
    except NotCorrectMessage as e:
        _logger.exception(e)
        await message.answer(e)
        return
    await message.answer(
        text=f"telegram ID {message.text} добавлен",
        reply_markup=keyboard
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()
