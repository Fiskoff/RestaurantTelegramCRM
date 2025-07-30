from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.models import Task


def format_tasks_list(tasks: list[Task], title: str) -> str:
    if not tasks:
        return ""

    result = f"<b>{title}</b>\n"
    for i, task in enumerate(tasks, 1):
        result += f"{i}. {task.title}\n"
    return result


def build_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        button = InlineKeyboardButton(
            text=task.title,
            callback_data=f"select_tasks:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)