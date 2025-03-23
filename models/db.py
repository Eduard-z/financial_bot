import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import Dict, List, Tuple, Any

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


def insert(table: str, column_values: Dict) -> Dict[str, Any]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        columns = ", ".join(column_values.keys())
        values = tuple(column_values.values())
        placeholders = ", ".join(['%s'] * len(column_values.keys()))

        cursor.execute(
            f"INSERT INTO {table} "
            f"({columns}) "
            f"VALUES ({placeholders}) RETURNING *",
            values)
        conn.commit()
        return cursor.fetchone()


def delete(table: str, column_values: Dict) -> Dict[str, Any] | None:
    row_exists = fetchone(table, column_values)
    if row_exists:
        deleted_row = delete_by_id(table, row_exists['id'])
        return deleted_row


def delete_by_id(table: str, row_id: int) -> Dict[str, Any] | None:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"DELETE FROM {table} WHERE id={row_id} RETURNING *")
        conn.commit()
        return cursor.fetchone()


def fetch_by_id(table: str, columns: List[str], row_id: int) -> Dict[str, Any] | None:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        columns_joined = ", ".join(columns)
        cursor.execute(f"SELECT {columns_joined} FROM {table} WHERE id={row_id}")
        conn.commit()
        return cursor.fetchone()


def fetchone(table: str, column_values: Dict) -> Dict[str, Any] | None:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        columns = ", ".join(column_values.keys())
        cursor.execute(
            f"SELECT id, {columns} FROM {table} "
            f"WHERE amount='{column_values['amount']}' "
            f"AND category_codename='{column_values['category_codename']}' "
            f"AND user_id='{column_values['user_id']}' "
            "ORDER BY id DESC limit 1"
        )
        return cursor.fetchone()


def fetchall(table: str, columns: List[str]) -> List[Dict]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        columns_joined = ", ".join(columns)
        cursor.execute(f"SELECT {columns_joined} FROM {table}")
        return cursor.fetchall()


def fetchall_by_user(table: str, columns: List[str], user_id: int) -> List[Dict]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        columns_joined = ", ".join(columns)
        cursor.execute(f"SELECT {columns_joined} FROM {table} "
                       f"WHERE user_id='{user_id}'")
        return cursor.fetchall()


def get_cursor():
    return conn.cursor()


def calculate_sum_for_today(table: str, user_id: int) -> float:
    with conn.cursor() as cursor:
        cursor.execute("SELECT sum(amount) "
                       f"FROM {table} "
                       "WHERE date(created)=date(current_date) "
                       f"AND user_id='{user_id}'"
        )
        return cursor.fetchone()[0]


def calculate_sum_by_month(table: str, report_year: int, report_month: int, user_ids: Tuple[int]) -> List[Dict]:
    placeholders = ", ".join(['%s'] * len(user_ids))
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT sum(amount), category_codename "
            f"FROM {table} "
            "WHERE date(created) "
            f"BETWEEN make_date({report_year}, {report_month}, 1) "
            f"AND (make_date({report_year}, {report_month}, 1) + make_interval(0, 1, 0, -1)) "
            f"AND user_id IN ({placeholders}) "
            "GROUP BY category_codename",
            vars=user_ids
        )
        return cursor.fetchall()


def last_expenses(user_id: int) -> List[Dict]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT e.id, e.amount, c.name "
                       "FROM expense e LEFT JOIN category c "
                       "ON c.codename=e.category_codename "
                       f"WHERE user_id='{user_id}' "
                       "ORDER BY created DESC limit 10"
        )
        return cursor.fetchall()


def insert_family_account(table: str, column_values: Dict) -> List[Dict]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        try:
            columns = ", ".join(column_values.keys())
            values = tuple(column_values.values())

            execute_values(
                cursor,
                f"INSERT INTO {table} "
                f"({columns}) "
                f"VALUES %s RETURNING user_id",
                [values, values[::-1]]
            )
            conn.commit()
        except Exception as err:
            # откат изменений в случае ошибки
            conn.rollback()
            print(f"Transaction failed: {err}")
            
        return cursor.fetchall()


def delete_family_account(table: str, user_id: int, family_id: int) -> List[Dict]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"DELETE FROM {table} "
            f"WHERE (user_id='{user_id}' AND family_id='{family_id}') "
            f"OR (user_id='{family_id}' AND family_id='{user_id}') RETURNING user_id")
        conn.commit()
        return cursor.fetchall()


def _init_db():
    with conn.cursor() as cursor:
        """Инициализирует БД"""
        with open(os.path.join("models", "createdb.sql"), mode="r", encoding="utf-8") as f:
            sql = f.read()
        cursor.execute(sql)
        conn.commit()


def check_db_exists():
    with conn.cursor() as cursor:
        """Проверяет, инициализирована ли БД, если нет — инициализирует"""
        cursor.execute("SELECT tablename FROM pg_catalog.pg_tables "
                       "WHERE schemaname='public' AND tablename='expense'")
        table_exists = cursor.fetchall()
        if table_exists:
            return
        _init_db()


check_db_exists()
