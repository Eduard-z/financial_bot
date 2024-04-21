"""Сервер Telegram бота, запускаемый непосредственно"""
import os
import logging
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties

from handlers import router


load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")


async def main() -> None:
    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot,
        skip_updates=True,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
