from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.models import Task


def build_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks:
        button = InlineKeyboardButton(
            text=f"{task.title}",
            callback_data=f"select_tasks:{task.task_id}"
        )
        buttons.append([button])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_tasks_list(tasks: list[Task], header: str) -> str:
    if not tasks:
        return ""
    lines = [f"<b>{header}</b>"]
    for task in tasks:
        deadline = task.deadline.strftime("%d.%m.%Y %H:%M")
        lines.append(f"• {task.title} (Дедлайн: {deadline})")
    return "\n".join(lines) + "\n"