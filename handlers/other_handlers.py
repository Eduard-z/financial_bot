from aiogram import types, F, Router
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command

from lexicon import LEXICON_RU
from middlewares import AllowAdminsOnlyMiddleware

router = Router()
router.message.middleware(AllowAdminsOnlyMiddleware())


@router.message(Command("id"))
@router.message(F.text == LEXICON_RU["my_id"])
async def send_id_handler(message: types.Message, _logger):
    _logger.info("User asked for their telegram ID")
    _logger.debug(f"telegram ID sent: {message.from_user.id}")
    await message.answer(
        text=f"Твой ID: {message.from_user.id}",
        reply_markup=ReplyKeyboardRemove()
    )
