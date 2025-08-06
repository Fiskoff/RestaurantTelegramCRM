from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.task_service import TaskService
from core.models.base_model import TaskStatus


staff_tasks_router = Router()


@staff_tasks_router.message(Command("staff_tasks"))
async def get_staff_task(message: Message):
    staff_tasks = await TaskService.get_staff_tasks()
    temp_list = []
    for i, task in enumerate(staff_tasks, 1):
        if task.status == TaskStatus.COMPLETED:
            temp_list.append(f"{i}. {task.executor.full_name}-{task.executor.position}:\n(✅ Выполнена) {task.title}\n{task.description}\n\n")
        elif task.status == TaskStatus.OVERDUE:
            temp_list.append(f"{i}. {task.executor.full_name}-{task.executor.position}:\n(❌ Просрочена) {task.title}\n{task.description}\n\n")
        else:
            temp_list.append(f"{i}. {task.executor.full_name}-{task.executor.position}:\n(⏳ В работе) {task.title}\n{task.description}\n\n")
    tasks_str = "\n".join(temp_list)
    await message.answer(f"Все задачи сотрудников:\n{tasks_str}")