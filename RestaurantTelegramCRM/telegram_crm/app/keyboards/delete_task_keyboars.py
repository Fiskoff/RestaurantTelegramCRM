from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.models import Task


def build_delete_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        if task.executor:
            executor_info = f"{task.executor.full_name} ({task.executor.position})"
        else:
            executor_info = "Исполнитель не назначен"

        button = InlineKeyboardButton(
            text=f"{task.title} - {executor_info}",
            callback_data=f"delete_task:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_update_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        if task.executor:
            executor_info = f"{task.executor.full_name} ({task.executor.position})"
        else:
            executor_info = "Исполнитель не назначен"

        button = InlineKeyboardButton(
            text=f"{task.title} - {executor_info}",
            callback_data=f"update_task:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)