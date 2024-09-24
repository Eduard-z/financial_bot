import os
from dotenv import load_dotenv
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту
    admin_ids: list[int]  # Список id администраторов бота


@dataclass
class Config:
    tg_bot: TgBot


# Создаем функцию, которая будет читать файл .env и возвращать
# экземпляр класса Config с заполненными полями token и admin_ids
def load_config() -> Config:
    load_dotenv()
    return Config(
        tg_bot=TgBot(
            token=os.getenv("BOT_TOKEN"),
            admin_ids=list(map(int, os.getenv("ACCESS_ID").split(",")))
        )
    )
