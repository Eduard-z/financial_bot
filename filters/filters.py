import re

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from helpers import is_telegram_id


# фильтр будет просто проверять callback_data у объекта CallbackQuery
# на то, что он состоит из цифр
class IsDigitCallbackData(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.isdigit()


class IsExpenseFilter(BaseFilter):
    async def __call__(self, message: Message, _logger) -> bool | dict[str, str]:
        _logger.debug('Попали внутрь фильтра %s', __class__.__name__)
        pattern = r"^(\d+,?\.?\d*)\s+([\w\s]+)$"
        search = re.fullmatch(pattern, message.text)
        if search:
            return {"amount": search.group(1), "product": search.group(2)}
        return False


class IsDeleteExpenseFilter(BaseFilter):
    async def __call__(self, message: Message, _logger) -> bool | dict[str, str]:
        _logger.debug('Попали внутрь фильтра %s', __class__.__name__)
        pattern = r"^-\s*(\d+,?\.?\d*)\s+([\w\s]+)$"
        search = re.fullmatch(pattern, message.text)
        if search:
            return {"amount": search.group(1), "product": search.group(2)}
        return False


class IsTelegramIdFilter(BaseFilter):
    async def __call__(self, message: Message, _logger) -> bool:
        _logger.debug('Попали внутрь фильтра %s', __class__.__name__)
        return is_telegram_id(message.text)
