""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
import pytz
from typing import List, NamedTuple, Optional

from . import db
from exceptions import NotCorrectMessage
from .categories import Categories, Category
from .family_accounts import get_family_accounts


class Expense(NamedTuple):
    """Структура добавленного в БД нового расхода"""
    id: Optional[int]
    user_id: int
    amount: float
    category_name: str


def add_expense(amount: str, product: str, raw_message: str, user_id: int) -> Expense | bool:
    """Добавляет новое сообщение.
    Принимает на вход сумму и товар."""
    validated_expense = _validate_amount(amount)
    category = _validate_product(product)

    inserted_row = db.insert("expense", {
        "user_id": user_id,
        "amount": validated_expense,
        "created": _get_now_formatted(),
        "category_codename": category.codename,
        "raw_text": raw_message
    })
    if inserted_row:
        return Expense(id=inserted_row['id'],
                       user_id=inserted_row['user_id'],
                       amount=inserted_row['amount'],
                       category_name=category.name
        )
    else:
        return False


def delete_expense(amount: str, product: str, user_id: int) -> Expense | bool:
    """Удаляет расход.
    Принимает на вход сумму и товар."""
    validated_expense = _validate_amount(amount)
    category = _validate_product(product)

    deleted_row = db.delete("expense", {
        "user_id": user_id,
        "amount": validated_expense,
        "category_codename": category.codename
    })
    if deleted_row:
        return Expense(id=deleted_row['id'],
                       user_id=deleted_row['user_id'],
                       amount=deleted_row['amount'],
                       category_name=category.name
        )
    else:
        return False


def delete_expense_by_id(row_id: int) -> str:
    """Удаляет расход по его идентификатору"""
    if isinstance(row_id, int):
        deleted_row = db.delete_by_id("expense", row_id)
        if deleted_row:
            return f"Expense #{deleted_row['id']} has been deleted"
        else:
            return f"Expense #{deleted_row['id']} does not exist any more"
    else:
        return "Fail: expense id is not a number"


def get_today_statistics(user_id: int) -> str:
    """Возвращает строкой статистику расходов за сегодня"""
    all_today_expenses = db.calculate_sum_for_today("expense", user_id)
    if not all_today_expenses:
        return "Сегодня ещё нет расходов"
    # cursor.execute("select sum(amount) "
    #                "from expense where date(created)=date('now', 'localtime') "
    #                f"and user_id='{user_id}' "
    #                "and category_codename in (select codename "
    #                "from category where is_base_expense=true)")
    # result = cursor.fetchone()
    # base_today_expenses = result[0] if result[0] else 0
    return (f"Расходы сегодня:\n"
            f"всего — {round(all_today_expenses, 2)} руб.\n"
            # f"базовые — {base_today_expenses} руб. из {_get_budget_limit()} руб.\n\n"
            f"За текущий месяц: /month")


def get_month_statistics(user_id: int, month: str) -> List[Expense]:
    """Возвращает строкой статистику расходов за месяц"""
    now = _get_now_datetime()
    current_year = now.year
    current_month = now.month

    all_family_accounts = get_family_accounts(user_id)
    family_user_ids = tuple(row.family_id for row in all_family_accounts)
    if not family_user_ids:
        user_ids = (user_id,)
    elif family_user_ids:
        user_ids = family_user_ids + (user_id,)
    else:
        raise Exception(f"Invalid {family_user_ids}")

    if month == "current_month":
        all_month_expenses = db.calculate_sum_by_month("expense", current_year, current_month, user_ids)
    elif 1 < current_month <= 12:
        reporting_month = current_month - 1
        all_month_expenses = db.calculate_sum_by_month("expense", current_year, reporting_month, user_ids)
    elif current_month == 1:
        reporting_year = current_year - 1
        all_month_expenses = db.calculate_sum_by_month("expense", reporting_year, 12, user_ids)
    else:
        raise Exception("Invalid month")

    month_expenses = [
        Expense(id=None,
                user_id=user_ids[0],
                amount=round(row['sum'], 2),
                category_name=_validate_product(row['category_codename']).name
        )
        for row in all_month_expenses
    ]

    return month_expenses


def last(user_id: int) -> List[Expense]:
    """Возвращает последние несколько расходов"""
    get_last_expenses = db.last_expenses(user_id)
    last_expenses = [
        Expense(id=row['id'], user_id=user_id, amount=row['amount'], category_name=row['name'])
        for row in get_last_expenses
    ]
    return last_expenses


def _validate_amount(amount: str) -> float:
    """Проверяет сумму из пришедшего сообщения о новом расходе."""
    try:
        amount = float(amount.replace(",", "."))
    except TypeError:
        raise NotCorrectMessage(
            "Неверная сумма. Напишите сообщение в формате, "
            "например:\n1.8 метро")

    return round(amount, 2)


def _validate_product(product: str) -> Category:
    """Проверяет товар из пришедшего сообщения о новом расходе."""
    category = Categories().get_category(product.lower())
    if not category:
        raise NotCorrectMessage(
            "Неверный товар. Напишите сообщение в формате, "
            "например:\n1.8 метро")

    return category


def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")


def _get_now_datetime() -> datetime.datetime:
    """Возвращает сегодняшний datetime с учётом временной зоны Минск."""
    tz = pytz.timezone("Europe/Minsk")
    now = datetime.datetime.now(tz)
    return now


def _get_budget_limit() -> int:
    """Возвращает дневной лимит трат для основных базовых трат"""
    [budget_limit] = db.fetchall("budget", ["daily_limit"])
    return budget_limit["daily_limit"]
