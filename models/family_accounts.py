from typing import NamedTuple, Optional, List

from . import db
from exceptions import NotCorrectMessage


class FamilyAccount(NamedTuple):
    """Структура добавленного в БД семейного аккаунта"""
    id: Optional[int]
    user_id: int
    family_id: int


def link_family_accounts(user_id: int, family_id: str) -> FamilyAccount:
    """Добавляет введённый telegram ID.
    Принимает на вход ID юзера и семейный ID."""
    family_id = _validate_account(family_id)

    """Сделать 2 записи"""
    db.insert("family_account", {
        "user_id": user_id,
        "family_id": family_id
    })
    db.insert("family_account", {
        "user_id": family_id,
        "family_id": user_id
    })

    return FamilyAccount(id=None,
                         user_id=user_id,
                         family_id=family_id)


def get_family_accounts(user_id: int) -> List[FamilyAccount]:
    """Возвращает объекты семейных аккаунтов"""
    cursor = db.get_cursor()
    cursor.execute("select id, user_id, family_id "
                   f"from family_account where user_id='{user_id}'")
    result = cursor.fetchall()

    all_family_accounts = [
        FamilyAccount(id=row[0], user_id=row[1], family_id=row[2])
        for row in result
    ]
    return all_family_accounts


def delete_family_account_by_id(row_id: int, user_id: int) -> str:
    """Удаляет семейный аккаунт (и связанный с ним основной) по его идентификатору"""
    cursor = db.get_cursor()
    cursor.execute("select id, user_id, family_id "
                   f"from family_account where id='{row_id}'")
    result = cursor.fetchone()

    if result[1] != user_id:
        return "It's not your family account"
    elif result[1] == user_id:
        db.delete_by_id("family_account", row_id)
        cursor.execute("select id from family_account "
                       f"where user_id='{result[2]}' and family_id='{result[1]}'")
        db.delete_by_id("family_account", cursor.fetchone()[0])
        return f"Family account #{row_id} has been deleted"
    else:
        return "Fail: family account id is not a number"


def _validate_account(account_id: str) -> int:
    """Поверяет telegram ID."""
    try:
        account = int(account_id)
    except TypeError:
        raise NotCorrectMessage("Не могу понять сообщение. Введите telegram ID")

    return account
