from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

def create_deadline_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="1 день", callback_data="deadline:1d"),
            InlineKeyboardButton(text="2 дня", callback_data="deadline:2d"),
        ],
        [
            InlineKeyboardButton(text="1 неделя", callback_data="deadline:1w"),
            InlineKeyboardButton(text="2 недели", callback_data="deadline:2w"),
        ],
        [
            InlineKeyboardButton(text="Бессрочно", callback_data="deadline:never"),
        ],
        [
            InlineKeyboardButton(text="Указать вручную", callback_data="deadline:manual"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def calculate_deadline_from_callback(callback_data: str, base_time: datetime = None) -> datetime | None:
    if not base_time:
        from zoneinfo import ZoneInfo
        base_time = datetime.now(ZoneInfo("Asia/Krasnoyarsk"))

    if callback_data == "deadline:1d":
        return base_time + timedelta(days=1)
    elif callback_data == "deadline:2d":
        return base_time + timedelta(days=2)
    elif callback_data == "deadline:1w":
        return base_time + timedelta(weeks=1)
    elif callback_data == "deadline:2w":
        return base_time + timedelta(weeks=2)
    elif callback_data == "deadline:never":
        return None
    elif callback_data == "deadline:manual":
        return None
    else:
        return None