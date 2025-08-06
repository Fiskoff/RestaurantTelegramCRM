from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.models import Task


def format_tasks_list(tasks: list[Task], header: str) -> str:
    if not tasks:
        return ""

    task_lines = []
    for i, task in enumerate(tasks, 1):
        if task.executor:
            executor_info = f"{task.executor.full_name} ({task.executor.position})"
        else:
            executor_info = "Для всего сектора"

        task_lines.append(
            f"{i}. <b>{task.title}</b>\n"
            f"{executor_info}\n"
            f"Описание задачи: {task.description}\n"
        )

    return f"<b>{header}</b>\n" + "\n".join(task_lines) if task_lines else ""


def build_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        if task.executor:
            executor_display = f"{task.executor.full_name} ({task.executor.position})"
        else:
            executor_display = "Для всего сектора"

        button = InlineKeyboardButton(
            text=f"{task.title} - {executor_display}",
            callback_data=f"select_tasks:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)