import os
import psycopg2
from typing import Dict, List, Tuple

from config_data.config import Config, load_config


# Загружаем конфиг в переменную config
config: Config = load_config()

# conn = sqlite3.connect(os.path.join("db", "finance.db"))
try:
    # пытаемся подключиться к базе данных
    conn = psycopg2.connect(
        dbname=config.db.database,
        user=config.db.db_user,
        password=config.db.db_password,
        host=config.db.db_host,
        port=config.db.db_port
    )
except Exception as e:
    # в случае сбоя подключения будет выведено сообщение в STDOUT
    print(f"Can't establish connection to database: {e}")
cursor = conn.cursor()


def insert(table: str, column_values: Dict):
    columns = ", ".join(column_values.keys())
    values = tuple(column_values.values())
    placeholders = ", ".join(['%s'] * len(column_values.keys()))
    cursor.execute(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    conn.commit()


def delete(table: str, column_values: Dict) -> bool:

    if fetchone(table, column_values):
        cursor.execute(
            f"delete from {table} "
            f"where amount='{column_values['amount']}' "
            f"AND category_codename='{column_values['category_codename']}' "
            f"AND user_id='{column_values['user_id']}' "
            f"AND id in (select id from {table} "
            f"where amount='{column_values['amount']}' "
            f"AND category_codename='{column_values['category_codename']}' "
            "order by id DESC limit 1)"
        )
        conn.commit()
        return True


def delete_by_id(table: str, row_id: int) -> None:
    cursor.execute(f"delete from {table} where id={row_id}")
    conn.commit()


def fetchone(table: str, column_values: Dict) -> List[Tuple]:
    columns = ', '.join(column_values.keys())
    cursor.execute(
        f"SELECT id, {columns} FROM {table} "
        f"where amount='{column_values['amount']}' "
        f"AND category_codename='{column_values['category_codename']}' "
        f"AND user_id='{column_values['user_id']}'"
    )
    return cursor.fetchone()


def fetchall(table: str, columns: List[str]) -> List[Dict]:
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table}")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def get_cursor():
    return cursor


def _init_db():
    """Инициализирует БД"""
    with open(os.path.join("models", "createdb.sql"), mode="r", encoding="utf-8") as f:
        sql = f.read()
    cursor.execute(sql)
    conn.commit()


def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    cursor.execute("SELECT tablename FROM pg_catalog.pg_tables "
                   "WHERE schemaname='public' AND tablename='expense'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()


check_db_exists()
