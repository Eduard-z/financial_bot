import os
from dotenv import load_dotenv
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    database: str         # Название базы данных
    db_host: str          # URL-адрес базы данных
    db_port: int          # 5432 by default
    db_user: str          # Username пользователя базы данных
    db_password: str      # Пароль к базе данных


@dataclass
class TgBot:
    token: str            # Токен для доступа к телеграм-боту
    admin_ids: list[int]  # Список id администраторов бота


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig


# Создаем функцию, которая будет читать файл .env и возвращать
# экземпляр класса Config с заполненными полями token и admin_ids
def load_config() -> Config:
    load_dotenv()
    return Config(
        tg_bot=TgBot(
            token=os.getenv("BOT_TOKEN"),
            admin_ids=list(map(int, os.getenv("ACCESS_ID").split(",")))
        ),
        db=DatabaseConfig(
            database=os.getenv("DB_NAME"),
            db_host=os.getenv("DB_HOST"),
            db_port=int(os.getenv("DB_PORT")),
            db_user=os.getenv("DB_USER"),
            db_password=os.getenv("DB_PASSWORD")
        )
    )
