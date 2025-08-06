from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.task_service import TaskService
from core.models.base_model import TaskStatus
from core.models.base_model import SectorStatus


staff_tasks_router = Router()


@staff_tasks_router.message(Command("staff_tasks"))
async def get_staff_task(message: Message):
    staff_tasks = await TaskService.get_staff_tasks()
    temp_list = []

    sector_names = {
        SectorStatus.BAR: "Бар",
        SectorStatus.HALL: "Зал",
        SectorStatus.KITCHEN: "Кухня"
    }

    for i, task in enumerate(staff_tasks, 1):
        if task.executor:
            executor_info = f"{task.executor.full_name}-{task.executor.position}"
        else:
            sector_name = sector_names.get(task.sector_task, "Неизвестный сектор")
            executor_info = f"Весь сектор ({sector_name})"

        if task.status == TaskStatus.COMPLETED:
            status_text = "✅ Выполнена"
        elif task.status == TaskStatus.OVERDUE:
            status_text = "❌ Просрочена"
        else:
            status_text = "⏳ В работе"

        temp_list.append(f"{i}. {executor_info}:\n({status_text}) {task.title}\n{task.description}\n\n")

    if temp_list:
        tasks_str = "\n".join(temp_list)
        await message.answer(f"Все задачи сотрудников:\n{tasks_str}")
    else:
        await message.answer("Нет задач для отображения")