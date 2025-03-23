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
    family_id: int = _validate_account(family_id)

    """Сделать 2 записи"""
    inserted_rows = db.insert_family_account("family_account", {
        "user_id": user_id,
        "family_id": family_id
    })

    return FamilyAccount(id=None,
                         user_id=inserted_rows[0]['user_id'],
                         family_id=inserted_rows[1]['user_id'])


def get_family_accounts(user_id: int) -> List[FamilyAccount]:
    """Возвращает объекты семейных аккаунтов"""
    family_accounts = db.fetchall_by_user("family_account", ["id", "user_id", "family_id"], user_id)

    all_family_accounts = [
        FamilyAccount(id=row['id'], user_id=row['user_id'], family_id=row['family_id'])
        for row in family_accounts
    ]
    return all_family_accounts


def delete_family_account_by_id(row_id: int, user_id: int) -> str:
    """Удаляет семейный аккаунт (и связанный с ним основной) по его идентификатору"""
    find_family_account = db.fetch_by_id("family_account", ["id", "user_id", "family_id"], row_id)

    if find_family_account['user_id'] != user_id:
        return "It's not your family account"
    elif find_family_account['user_id'] == user_id:
        deleted_rows = db.delete_family_account("family_account", user_id, find_family_account['family_id'])
        return f"Family account #{deleted_rows[1]['user_id']} has been deleted"
    else:
        return "Fail: family account id is not a number"


def _validate_account(account_id: str) -> int:
    """Поверяет telegram ID."""
    try:
        account = int(account_id)
    except ValueError:
        raise NotCorrectMessage("Не могу понять сообщение. Введите telegram ID")

    return account
