def is_telegram_id(telegram_id: str) -> bool:
    return telegram_id.isdigit() and 1 < len(telegram_id) <= 10
