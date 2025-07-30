from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.task_service import TaskService


overdue_task = Router()


@overdue_task.message(Command("all_overdue_task"))
async def get_all_overdue_task_staff(message: Message):
    overdue_tasks = await TaskService.get_all_overdue_tasks()
    task_list = []
    for i, task in enumerate(overdue_tasks, 1):
        task_list.append(
            f"{i}. Задача: {task.title}\n"
            f"   Сотрудник: {task.executor_id}\n"
        )

    response = "Список просроченных задач работников:\n" + "\n".join(task_list)
    await message.answer(response)
