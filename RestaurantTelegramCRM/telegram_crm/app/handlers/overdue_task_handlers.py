from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.task_service import TaskService

overdue_task = Router()


@overdue_task.message(Command("all_overdue_task"))
async def get_all_overdue_task_staff(message: Message):
    overdue_tasks_with_users = await TaskService.get_all_overdue_tasks()
    if not overdue_tasks_with_users:
        await message.answer("Нет просроченных задач.")
        return

    task_list = []
    for i, (task, user) in enumerate(overdue_tasks_with_users, 1):
        deadline_str = task.deadline.strftime("%d.%m.%Y %H:%M")

        task_info = f"{i}. Задача: {task.title}\n"
        task_info += f"   Дедлайн: {deadline_str}\n"

        if user:
            task_info += f"   Исполнитель: {user.full_name}\n"
            if user.position:
                task_info += f"   Должность: {user.position}\n"
        else:
            task_info += f"   Исполнитель: Не назначен\n"

        task_list.append(task_info)

    response = "Список просроченных задач работников:\n\n" + "\n".join(task_list)
    await message.answer(response)