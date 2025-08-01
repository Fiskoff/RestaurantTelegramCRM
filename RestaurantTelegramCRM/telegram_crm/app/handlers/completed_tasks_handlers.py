import asyncio
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

from app.services.task_service import TaskService
from app.keyboards.select_complete_tasks_keyboards import build_completed_tasks_keyboard
from app.keyboards.task_reply_keyboard import get_chek_task_action_keyboard


completed_tasks_router = Router()


@completed_tasks_router.message(F.text == "✅ Задача закрыта")
async def close_task(message: Message):

    await message.answer(
        "Вы закрыли задачу, она считается выполненной\n",
    )


@completed_tasks_router.message(Command("completed_tasks"))
async def get_completed_task(message: Message):
    completed_tasks = await TaskService.get_completed_tasks()

    if not completed_tasks:
        await message.answer("Выполненных задач нет")
        return

    keyboard = build_completed_tasks_keyboard(completed_tasks)
    await message.answer("Выберите задачу:", reply_markup=keyboard)


@completed_tasks_router.callback_query(lambda c: c.data and c.data.startswith('select_completed_tasks:'))
async def get_completed_task_by_id(callback_query: CallbackQuery, state: FSMContext):
    task_id_str = callback_query.data.split(':')[1]
    task_id = int(task_id_str)

    task = await TaskService.get_task_by_id_and_staff(task_id)

    await state.update_data(task_id=task_id)

    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    deadline_with_tz = task.deadline.replace(tzinfo=kemerovo_tz)
    completed_at_with_tz = task.completed_at.replace(tzinfo=kemerovo_tz)

    deadline_str = deadline_with_tz.strftime("%d.%m.%Y %H:%M")
    completed_at_str = completed_at_with_tz.strftime("%d.%m.%Y %H:%M")
    response_text = (
        f"«{task.title}»\n"
        f"Описание задачи: {task.description}\n"
        f"Дедлайн: {deadline_str}\n"
        f"\n"
        f"Сотрудник: {task.executor.full_name} - {task.executor.position}\n"
        f"Выполнено: {completed_at_str}\n"
        f"Комментарий к выполненной задачи:\n"
        f"{task.comment or 'Комментарий не был оставлен'}\n"
    )

    if task.photo_url:
        photo_urls = [url.strip() for url in task.photo_url.split(',') if url.strip()]

        if photo_urls:
            if len(photo_urls) == 1:
                await callback_query.message.answer_photo(photo=photo_urls[0], caption=response_text)
            else:
                media_group = [InputMediaPhoto(media=url, caption=response_text if i == 0 else None) for i, url in
                               enumerate(photo_urls)]
                await callback_query.message.answer_media_group(media=media_group)

        else:
            await callback_query.message.answer(response_text)
    else:
        await callback_query.message.answer(response_text)

    chek_keyboard = get_chek_task_action_keyboard()
    await callback_query.message.answer(
        "Проверьте правильность выпаленного задания\n"
        "Выберите\n"
        "✅ Задача закрыта - вас устраивает полученный результат\n"
        "❌ Доработать - результат вас не устроил",
        reply_markup=chek_keyboard
    )
    await callback_query.answer()



