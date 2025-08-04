from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.models import Task


def build_delete_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        button = InlineKeyboardButton(
            text=f"{task.title} - {task.executor.full_name}({task.executor.position})",
            callback_data=f"delete_task:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_update_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        button = InlineKeyboardButton(
            text=f"{task.title} - {task.executor.full_name}({task.executor.position})",
            callback_data=f"update_task:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)