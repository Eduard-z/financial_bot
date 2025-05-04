from aiogram import types, Router
from aiogram.filters import CommandStart

from lexicon import LEXICON_RU
from middlewares import NonUserThrottlingMiddleware
from models import User


router = Router()
router.message.middleware(NonUserThrottlingMiddleware())


@router.message(CommandStart())
async def send_welcome(message: types.Message, _logger):
    _logger.info("User launched the bot")
    try:
        User.insert_table()
        # User.add_user(message.from_user.id)
        answer_message = LEXICON_RU["greet"].format(name=message.from_user.full_name)
    except Exception as e:
        _logger.exception(e)
    else:
        await message.answer(text=answer_message)
