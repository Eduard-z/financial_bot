from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from cachetools import TTLCache


class UserThrottlingMiddleware(BaseMiddleware):

    # Максимальный размер кэша - 1000 ключей, а время жизни ключа - 1 секунда
    CACHE = TTLCache(maxsize=1000, ttl=1)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        logger = data.get("_logger")
        logger.debug(
            'Вошли в миддлварь %s, тип события %s',
            __class__.__name__,
            event.__class__.__name__
        )

        user: User = data.get('event_from_user')
        if user.id in UserThrottlingMiddleware.CACHE:
            return

        UserThrottlingMiddleware.CACHE[user.id] = True

        result = await handler(event, data)

        logger.debug('Выходим из миддлвари  %s', __class__.__name__)

        return result


class NonUserThrottlingMiddleware(BaseMiddleware):

    # Максимальный размер кэша - 1000 ключей, а время жизни ключа - 5 секунд
    CACHE = TTLCache(maxsize=1000, ttl=5)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        logger = data.get("_logger")
        logger.debug(
            'Вошли в миддлварь %s, тип события %s',
            __class__.__name__,
            event.__class__.__name__
        )

        user: User = data.get('event_from_user')
        if user.id in NonUserThrottlingMiddleware.CACHE:
            return

        NonUserThrottlingMiddleware.CACHE[user.id] = True

        result = await handler(event, data)

        logger.debug('Выходим из миддлвари  %s', __class__.__name__)

        return result
