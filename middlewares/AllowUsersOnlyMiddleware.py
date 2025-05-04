from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from helpers import is_telegram_id


class AllowUsersOnlyMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        logger = data.get("_logger")
        logger.debug(
            'Вошли в миддлварь %s, тип события %s',
            __class__.__name__,
            event.__class__.__name__
        )
        logger.debug(f"Admin IDs: {data.get('_admin_ids')}")

        user: User = data.get('event_from_user')
        if user and not is_telegram_id(str(user.id)) and user.id not in data.get("_admin_ids"):
            return

        result = await handler(event, data)

        logger.debug('Выходим из миддлвари  %s', __class__.__name__)

        return result
