""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
import pytz
from typing import List, NamedTuple, Optional

from . import db
from exceptions import NotCorrectMessage
from .categories import Categories


class Message(NamedTuple):
    """Структура распаршенного сообщения о новом расходе"""
    amount: float
    category_text: str


class Expense(NamedTuple):
    """Структура добавленного в БД нового расхода"""
    id: Optional[int]
    user_id: int
    amount: float
    category_name: str


def add_expense(amount: str, product: str, raw_message: str, user_id: int) -> Expense:
    """Добавляет новое сообщение.
    Принимает на вход сумму и товар."""
    validated_expense = _validate_amount(amount, product)
    category = Categories().get_category(
        validated_expense.category_text)
    inserted_row_id = db.insert("expense", {
        "user_id": user_id,
        "amount": validated_expense.amount,
        "created": _get_now_formatted(),
        "category_codename": category.codename,
        "raw_text": raw_message
    })
    return Expense(id=None,
                   user_id=user_id,
                   amount=validated_expense.amount,
                   category_name=category.name)


def delete_expense(amount: str, product: str, user_id: int) -> Expense:
    """Удаляет расход.
    Принимает на вход сумму и товар."""
    validated_expense = _validate_amount(amount, product)
    category = Categories().get_category(
        validated_expense.category_text)
    find_expense = db.fetchone("expense", {
        "user_id": user_id,
        "amount": validated_expense.amount,
        "created": _get_now_formatted(),
        "category_codename": category.codename
    })

    if find_expense:
        db.delete("expense", {
            "user_id": user_id,
            "amount": validated_expense.amount,
            "created": _get_now_formatted(),
            "category_codename": category.codename
        })
        return Expense(id=None,
                       user_id=None,
                       amount=validated_expense.amount,
                       category_name=category.name)
    else:
        return False


def delete_expense_by_id(row_id: int) -> str:
    """Удаляет расход по его идентификатору"""
    if isinstance(row_id, int):
        db.delete_by_id("expense", row_id)
        return f"Expense #{row_id} has been deleted"
    else:
        return "Fail: expense id is not a number"


def get_today_statistics(user_id: int) -> str:
    """Возвращает строкой статистику расходов за сегодня"""
    cursor = db.get_cursor()
    cursor.execute("select sum(amount) "
                   "from expense where date(created)=date('now', 'localtime') "
                   f"and user_id='{user_id}'")
    result = cursor.fetchone()
    if not result[0]:
        return "Сегодня ещё нет расходов"
    all_today_expenses = result[0]
    # cursor.execute("select sum(amount) "
    #                "from expense where date(created)=date('now', 'localtime') "
    #                f"and user_id='{user_id}' "
    #                "and category_codename in (select codename "
    #                "from category where is_base_expense=true)")
    # result = cursor.fetchone()
    # base_today_expenses = result[0] if result[0] else 0
    return (f"Расходы сегодня:\n"
            f"всего — {all_today_expenses} руб.\n"
            # f"базовые — {base_today_expenses} руб. из {_get_budget_limit()} руб.\n\n"
            f"За текущий месяц: /month")


def get_month_statistics(user_id: int) -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""
    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor = db.get_cursor()

    family_user_ids = _get_family_accounts_list(user_id)
    if not family_user_ids:
        user_ids = "(" + str(user_id) + ")"
    elif family_user_ids:
        user_ids = family_user_ids + (user_id,)
    else:
        raise Exception(f"Invalid {family_user_ids}")

    cursor.execute(f"select sum(amount), category_codename "
                   f"from expense where date(created) >= '{first_day_of_month}' "
                   f"and user_id in {user_ids} "
                   f"GROUP BY category_codename")
    result = cursor.fetchall()
    month_expenses = [
        Expense(id=0, user_id=user_ids[0], amount=row[0], category_name=row[1])
        for row in result
    ]

    return month_expenses


def get_past_month_statistics(user_id: int) -> str:
    """Возвращает строкой статистику расходов за прошлый месяц"""
    now = _get_now_datetime()
    current_year = now.year
    current_month = now.month

    if 1 < current_month <= 12:
        first_day_of_month = f'{current_year:04d}-{current_month - 1:02d}-01'
        last_day_of_month = f'{current_year:04d}-{current_month - 1:02d}-31'
    elif current_month == 1:
        first_day_of_month = f'{current_year - 1:04d}-{12:02d}-01'
        last_day_of_month = f'{current_year - 1:04d}-{12:02d}-31'
    else:
        raise Exception("Invalid month")

    cursor = db.get_cursor()
    family_user_ids = _get_family_accounts_list(user_id)
    if not family_user_ids:
        user_ids = "(" + str(user_id) + ")"
    elif family_user_ids:
        user_ids = family_user_ids + (user_id,)
    else:
        raise Exception(f"Invalid {family_user_ids}")

    cursor.execute(f"select sum(amount), category_codename "
                   f"from expense where "
                   f"date(created) BETWEEN '{first_day_of_month}' AND '{last_day_of_month}' "
                   f"and user_id in {user_ids} "
                   f"GROUP BY category_codename")
    result = cursor.fetchall()
    month_expenses = [
        Expense(id=0, user_id=user_ids[0], amount=row[0], category_name=row[1])
        for row in result
    ]

    return month_expenses


def last(user_id: int) -> List[Expense]:
    """Возвращает последние несколько расходов"""
    cursor = db.get_cursor()
    cursor.execute(
        "select e.id, e.amount, c.name "
        "from expense e left join category c "
        "on c.codename=e.category_codename "
        f"where user_id='{user_id}' "
        "order by created desc limit 10")
    rows = cursor.fetchall()
    last_expenses = [
        Expense(id=row[0], user_id=user_id, amount=row[1], category_name=row[2])
        for row in rows
    ]
    return last_expenses


def _validate_amount(amount: str, product: str) -> Message:
    """Поверяет сумму из пришедшего сообщения о новом расходе."""
    try:
        amount = float(amount.replace(",", "."))
    except TypeError:
        raise NotCorrectMessage(
            "Не могу понять сообщение. Напишите сообщение в формате, "
            "например:\n1.8 метро")

    return Message(amount=amount, category_text=product.lower())


def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")


def _get_now_datetime() -> datetime.datetime:
    """Возвращает сегодняшний datetime с учётом времненной зоны Минск."""
    tz = pytz.timezone("Europe/Minsk")
    now = datetime.datetime.now(tz)
    return now


def _get_budget_limit() -> int:
    """Возвращает дневной лимит трат для основных базовых трат"""
    return db.fetchall("budget", ["daily_limit"])[0]["daily_limit"]


def _get_family_accounts_list(user_id: int) -> tuple:
    """Возвращает список семейных аккаунтов"""
    cursor = db.get_cursor()
    cursor.execute("select id, family_id "
                   f"from family_account where user_id='{user_id}'")
    result = cursor.fetchall()

    all_family_accounts = tuple(row[1] for row in result)
    return all_family_accounts
