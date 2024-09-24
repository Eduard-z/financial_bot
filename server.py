"""Сервер Telegram бота, запускаемый непосредственно"""
import asyncio
import os
import logging
import logging.config
import yaml

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties

from config_data.config import Config, load_config
from handlers import other_handlers, handlers
from keyboards import set_main_menu
from middlewares import UserThrottlingMiddleware


# Загружаем конфиг логгера
with open(os.path.join("config_data", "logging_config.yaml"), 'rt') as f:
    config = yaml.safe_load(f.read())
logging.config.dictConfig(config)

# Инициализируем логгер
logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main() -> None:
    # Конфигурируем логирование
    logger.setLevel(logging.DEBUG)

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config()

    # Инициализируем бот и диспетчер
    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистриуем роутер в диспетчере
    dp.include_router(handlers.router)
    dp.include_router(other_handlers.router)

    # Здесь будем регистрировать миддлвари
    dp.update.outer_middleware(UserThrottlingMiddleware())

    #  Передаём логгер в хранилище проекта
    dp.workflow_data.update({'_logger': logger})

    # Настраиваем кнопку Menu
    await set_main_menu(bot)

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot,
        skip_updates=True,
        allowed_updates=dp.resolve_used_update_types(),
        # pass admin ids into middleware
        _admin_ids=config.tg_bot.admin_ids
    )


if __name__ == '__main__':
    asyncio.run(main())
