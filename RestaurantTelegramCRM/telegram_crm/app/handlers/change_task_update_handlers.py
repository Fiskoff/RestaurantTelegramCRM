from zoneinfo import ZoneInfo

from aiogram import F
from aiogram.types import Message, CallbackQuery

from app.handlers import change_task_router
from app.keyboards.delete_task_keyboars import build_update_tasks_keyboard
from app.services.task_service import TaskService


@change_task_router.message(F.text == "Изменить задачу")
async def change_task(message: Message):
    tasks = await TaskService.get_all_task()
    task_keyboard = build_update_tasks_keyboard(tasks)
    await message.answer("Выберите задачу для изменения:", reply_markup=task_keyboard)


@change_task_router.callback_query(lambda c: c.data and c.data.startswith('update_task:'))
async def start_change_task(callback_query: CallbackQuery):
    task_id_str = callback_query.data.split(':')[1]
    task_id = int(task_id_str)

    selected_task = await TaskService.get_task_by_id(task_id)

    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    deadline_with_tz = selected_task.deadline.replace(tzinfo=kemerovo_tz)
    await callback_query.message.answer(
        f"Выбранная задача для изменения:\n\n"
        f"Название: {selected_task.title}\n"
        f"Описание: {selected_task.description}\n"
        f"Сотрудник: {selected_task.executor.full_name} - {selected_task.executor.position}\n"
        f"Дедланй: {deadline_with_tz}\n"
    )
    await callback_query.message.answer(
        "Что вы хотите изменить?\n"
        "1 - Название\n"
        "2 - Описание\n"
        "3 - Сотрудник\n"
        "4 - Описание\n"
        "Отправите подходящее число"
    )
