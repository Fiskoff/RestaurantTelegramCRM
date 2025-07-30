from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.keyboards.select_all_task_keyboard import format_tasks_list, build_tasks_keyboard
from app.services.task_service import TaskService


my_task_router = Router()


@my_task_router.message(Command("my_tasks"))
async def get_my_tasks(message: Message):
    telegram_id = message.from_user.id
    tasks = await TaskService.get_all_task(telegram_id)

    if not tasks:
        await message.answer("У вас пока нет задач.")
        return

    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    current_time = datetime.now(kemerovo_tz)
    active_tasks = [t for t in tasks if t.deadline.replace(tzinfo=kemerovo_tz) > current_time]
    overdue_tasks = [t for t in tasks if t.deadline.replace(tzinfo=kemerovo_tz) <= current_time]

    active_text = format_tasks_list(active_tasks, "Активные задачи:")
    overdue_text = format_tasks_list(overdue_tasks, "Просроченные задачи:")

    full_text = active_text + "\n" + overdue_text if (active_text or overdue_text) else "Нет задач для отображения."

    await message.answer(full_text, parse_mode="HTML")

    keyboard = build_tasks_keyboard(tasks)
    await message.answer("Выберите задачу:", reply_markup=keyboard)


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
