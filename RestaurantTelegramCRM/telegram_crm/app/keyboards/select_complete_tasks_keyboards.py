from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.models import Task


def build_completed_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        button = InlineKeyboardButton(
            text=f"{task.title} - {task.executor.full_name}({task.executor.position})",
            callback_data=f"select_completed_tasks:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)