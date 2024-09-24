from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart

from lexicon import LEXICON_RU
from middlewares import NonUserThrottlingMiddleware

router = Router()
router.message.middleware(NonUserThrottlingMiddleware())


@router.message(CommandStart())
async def send_welcome(message: types.Message, _logger):
    _logger.info("User launched the bot")
    try:
        answer_message = LEXICON_RU["greet"].format(name=message.from_user.full_name)
    except Exception as e:
        _logger.exception(e)
    else:
        await message.answer(text=answer_message)


@router.message(Command(commands="help"))
@router.message(F.text == LEXICON_RU["help"])
async def help_menu_handler(message: types.Message, _logger):
    _logger.info("User asked for help")
    await message.answer(
        "Бот для учёта финансов\n\n"
        "Добавить расход: 12.5 такси\n"
        "Удалить расход: -12.5 такси\n"
        "Статистика за текущий месяц: /month\n"
        "Последние внесённые расходы: /expenses\n"
        "Категории трат: /categories",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("id"))
@router.message(F.text == LEXICON_RU["my_id"])
async def message_handler(message: types.Message, _logger):
    _logger.info("User asked for their telegram ID")
    _logger.debug(f"telegram ID sent: {message.from_user.id}")
    await message.answer(
        text=f"Твой ID: {message.from_user.id}",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(F.text.lower().__eq__("хуй"))
async def hui_special(message: types.Message, _logger):
    """Ответ на сообщение"""
    _logger.info("User typed hui")
    await message.answer("тебе")


@router.message(F.text.lower().__eq__("пизда"))
async def pizda_special(message: types.Message, _logger):
    """Ответ на сообщение"""
    _logger.info("User typed pizda")
    await message.answer("рулю")


# Этот хэндлер будет реагировать на сообщения типа "не текст"
@router.message(~F.text)
async def not_text_handler(message: types.Message, _logger):
    _logger.info(
        f"User sent not text: {message.model_dump_json(indent=4, exclude_none=True)}"
    )
    await message.answer("Я понимаю только текст!")


# Этот хэндлер будет реагировать на любые сообщения пользователя,
# не предусмотренные логикой работы бота
@router.message()
async def send_echo(message: types.Message, _logger):
    _logger.info(f"User typed an incorrect command: {message.text}")
    await message.answer(f"Это эхо! {message.text}")
