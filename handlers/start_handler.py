from aiogram import types, Router
from aiogram.filters import CommandStart

from lexicon import LEXICON_RU
from middlewares import NonUserThrottlingMiddleware
from models import users
from helpers import is_telegram_id


router = Router()
router.message.middleware(NonUserThrottlingMiddleware())


@router.message(CommandStart())
async def send_welcome(message: types.Message, _logger):
    _logger.info("User launched the bot")

    user_ids = users.get_user_ids()
    _logger.debug(f"Users IDs: {user_ids}")

    tg_id = message.from_user.id
    if not is_telegram_id(str(tg_id)):
        return

    if tg_id not in user_ids:
        try:
            users.add_user(message.from_user.id)
        except Exception as e:
            _logger.exception(e)

    answer_message = LEXICON_RU["greet"].format(name=message.from_user.full_name)
    await message.answer(text=answer_message)
