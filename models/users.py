from typing import NamedTuple, Optional, List

from . import db


class User(NamedTuple):
    """Структура добавленного в БД юзер аккаунта"""
    id: Optional[int]
    user_id: int


def add_user(user_id: int) -> User | bool:
    """Добавляет нового юзера"""
    inserted_row = db.insert("users", {
        "user_id": user_id
    })
    if inserted_row:
        return User(id=inserted_row['id'],
                    user_id=inserted_row['user_id'])
    else:
        return False


def get_user_ids() -> List[int]:
    """Возвращает айди всех юзеров приложения"""
    user_ids = db.fetchall("users", ["user_id"])

    return [row['user_id'] for row in user_ids]
