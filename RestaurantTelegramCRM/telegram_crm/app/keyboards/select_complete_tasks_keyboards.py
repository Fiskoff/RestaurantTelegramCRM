from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.models import Task


def build_completed_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        if task.executor:
            executor_info = f"{task.executor.full_name} ({task.executor.position})"
        else:
            executor_info = "Исполнитель не назначен"

        button_text = f"{task.title} - {executor_info}"

        button = InlineKeyboardButton(
            text=button_text,
            callback_data=f"select_completed_tasks:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)