from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.user_service import UserService


async def create_employee_selection_keyboard() -> InlineKeyboardMarkup:
    employees = await UserService.get_all_users()
    buttons = []
    for employee in employees:
        button = InlineKeyboardButton(
            text=f"{employee.position} - {employee.full_name}",
            callback_data=f"select_employee:{employee.telegram_id}"
        )
        buttons.append([button])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def create_sector_selection_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🍸 Бар", callback_data="select_sector:bar")],
        [InlineKeyboardButton(text="🍽️ Зал", callback_data="select_sector:hall")],
        [InlineKeyboardButton(text="👨‍🍳 Кухня", callback_data="select_sector:kitchen")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)