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