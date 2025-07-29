from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime  # Для форматирования дат

from app.services.task_service import TaskService
from app.keyboards.select_all_task_keyboard import select_all_tasks_keyboard


my_task_router = Router()


@my_task_router.message(Command("my_tasks"))
async def get_my_tasks(message: Message):
    keyboard = await select_all_tasks_keyboard(message.from_user.id)
    if keyboard.inline_keyboard:
        await message.answer("Выберите задачу:", reply_markup=keyboard)
    else:
        await message.answer("У вас пока нет задач.")


@my_task_router.callback_query(lambda c: c.data and c.data.startswith('select_tasks:'))
async def get_task_by_id(callback_query: CallbackQuery):
    try:
        task_id_str = callback_query.data.split(':')[1]
        task_id = int(task_id_str)
    except (IndexError, ValueError):
        await callback_query.answer("Ошибка обработки запроса.", show_alert=True)
        return

    task = await TaskService.get_task_by_id(task_id)
    deadline_str = task.deadline.strftime("%d.%m.%Y %H:%M")
    response_text = (
        f"«{task.title}»\n"
        f"Описание задачи: {task.description}\n"
        f"Дедлайн: {deadline_str}\n"
    )
    await callback_query.message.answer(response_text)
    await callback_query.answer()
