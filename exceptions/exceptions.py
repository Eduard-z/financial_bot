"""Кастомные исключения, генерируемые приложением"""


class NotCorrectMessage(Exception):
    """Некорректное сообщение в бот, которое не удалось распарсить"""

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        message = self.message
        return message

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"
