from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.task_service import TaskService


async def select_all_tasks_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    tasks = await TaskService.get_all_task(telegram_id)
    buttons = []
    for task in tasks:
        button = InlineKeyboardButton(
            text=f"{task.title}",
            callback_data=f"select_employee:{task.task_id}"
        )
        buttons.append([button])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard