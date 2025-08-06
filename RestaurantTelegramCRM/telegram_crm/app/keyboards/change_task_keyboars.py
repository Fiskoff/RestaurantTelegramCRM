from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.models import Task, SectorStatus


def build_delete_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        if task.executor:
            executor_display = f"{task.executor.full_name} ({task.executor.position})"
        else:
            if task.sector_task:
                sector_names = {
                    SectorStatus.BAR: "Бар",
                    SectorStatus.HALL: "Зал",
                    SectorStatus.KITCHEN: "Кухня"
                }
                sector_name = sector_names.get(task.sector_task, "Неизвестный сектор")
                executor_display = f"Весь сектор ({sector_name})"
            else:
                executor_display = "Исполнитель не назначен"

        button = InlineKeyboardButton(
            text=f"{task.title} - {executor_display}",
            callback_data=f"delete_task:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_update_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        if task.executor:
            executor_display = f"{task.executor.full_name} ({task.executor.position})"
        else:
            if task.sector_task:
                sector_names = {
                    SectorStatus.BAR: "Бар",
                    SectorStatus.HALL: "Зал",
                    SectorStatus.KITCHEN: "Кухня"
                }
                sector_name = sector_names.get(task.sector_task, "Неизвестный сектор")
                executor_display = f"Весь сектор ({sector_name})"
            else:
                executor_display = "Исполнитель не назначен"

        button = InlineKeyboardButton(
            text=f"{task.title} - {executor_display}",
            callback_data=f"update_task:{task.task_id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)