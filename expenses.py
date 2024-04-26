""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
import re
from typing import List, NamedTuple, Optional

import pytz

import db
import exceptions
from categories import Categories


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


def add_expense(raw_message: str, user_id: int) -> Expense:
    """Добавляет новое сообщение.
    Принимает на вход текст сообщения, пришедшего в бот."""
    parsed_message = _parse_message(raw_message)
    category = Categories().get_category(
        parsed_message.category_text)
    inserted_row_id = db.insert("expense", {
        "user_id": user_id,
        "amount": parsed_message.amount,
        "created": _get_now_formatted(),
        "category_codename": category.codename,
        "raw_text": raw_message
    })
    return Expense(id=None,
                   user_id=user_id,
                   amount=parsed_message.amount,
                   category_name=category.name)


def delete_expense(raw_message: str, user_id: int) -> Expense:
    """Удаляет расход.
    Принимает на вход текст сообщения, пришедшего в бот."""
    parsed_message = _parse_message(raw_message)
    category = Categories().get_category(
        parsed_message.category_text)

    deleted_amount = -int(parsed_message.amount)
    db.delete("expense", {
        "amount": deleted_amount,
        "created": _get_now_formatted(),
        "category_codename": category.codename,
        "raw_text": raw_message
    })
    return Expense(id=None,
                   user_id=None,
                   amount=parsed_message.amount,
                   category_name=category.name)


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
    cursor.execute("select sum(amount) "
                   "from expense where date(created)=date('now', 'localtime') "
                   f"and user_id='{user_id}' "
                   "and category_codename in (select codename "
                   "from category where is_base_expense=true)")
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Расходы сегодня:\n"
            f"всего — {all_today_expenses} руб.\n"
            f"базовые — {base_today_expenses} руб. из {_get_budget_limit()} руб.\n\n"
            f"За текущий месяц: /month")


def get_month_statistics(user_id: int) -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""
    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor = db.get_cursor()

    cursor.execute(f"select sum(amount), category_codename "
                   f"from expense where date(created) >= '{first_day_of_month}' "
                   f"and user_id='{user_id}' "
                   f"GROUP BY category_codename")
    result = cursor.fetchall()
    month_expenses = [
        Expense(id=0, user_id=user_id, amount=row[0], category_name=row[1])
        for row in result
    ]

    return month_expenses
    # (f"Расходы в текущем месяце:\n"
    #         f"всего — {all_today_expenses} руб.\n"
    #         f"базовые — {base_today_expenses} руб. из "
    #         f"{now.day * _get_budget_limit()} руб.")


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


def _parse_message(raw_message: str) -> Message:
    """Парсит текст пришедшего сообщения о новом расходе."""
    regexp_result = re.match(r"(-?[\d. ]+) (.*)", raw_message)
    if not regexp_result or not regexp_result.group(0) \
            or not regexp_result.group(1) or not regexp_result.group(2):
        raise exceptions.NotCorrectMessage(
            "Не могу понять сообщение. Напишите сообщение в формате, "
            "например:\n1.8 метро")

    amount = regexp_result.group(1).replace(" ", "")
    category_text = regexp_result.group(2).strip().lower()
    return Message(amount=amount, category_text=category_text)


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
