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
            f"{i}. {task.title}\n"
            f"   {task.executor_id}\n"
        )

    response = "Список всех работников:\n\n" + "\n\n".join(task_list)
    await message.answer(response)
