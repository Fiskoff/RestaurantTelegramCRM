from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

from app.services.task_service import TaskService
from app.keyboards.select_complete_tasks_keyboards import build_completed_tasks_keyboard
from app.keyboards.task_reply_keyboard import get_chek_task_action_keyboard


completed_tasks_router = Router()


class TaskCheckUpdateStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_deadline = State()


@completed_tasks_router.message(F.text == "❌ Доработать задачу")
async def start_chek_task(message: Message, state: FSMContext):
    user_data = await state.get_data()
    task_id = user_data.get('current_task_id')
    if not task_id:
        await message.answer("Ошибка: не удалось найти информацию о задаче. Пожалуйста, начните сначала.")
        await state.clear()
        return

    refine_task = await TaskService.get_task_by_id(task_id)
    if not refine_task:
        await message.answer("Ошибка: задача не найдена.")
        await state.clear()
        return

    await state.update_data(
        original_task_id=task_id,
        original_title=refine_task.title,
        original_description=refine_task.description,
        original_deadline=refine_task.deadline,
        original_executor_id=refine_task.executor_id,
        original_manager_id=refine_task.manager_id
    )

    new_title = f"(Доработать!) {refine_task.title}"
    await state.update_data(new_title=new_title)

    await message.answer(
        f"Задача будет активна под таким именем: {new_title}\n"
        f"\n"
        f"Опишите что нужно исправить:\n"
    )
    await state.set_state(TaskCheckUpdateStates.waiting_for_description)


@completed_tasks_router.message(TaskCheckUpdateStates.waiting_for_description)
async def process_new_description(message: Message, state: FSMContext):
    input_description = message.text

    user_data = await state.get_data()
    original_description = user_data.get('original_description', '')

    new_description = f"\nПояснение к исправлению:\n{input_description}\n\nСтарое описание:\n{original_description}"
    await state.update_data(new_description=new_description)

    await message.answer("Укажите дату и время окончания задачи \nВ формате: 01.01.2025 - 22:30")
    await state.set_state(TaskCheckUpdateStates.waiting_for_deadline)


@completed_tasks_router.message(TaskCheckUpdateStates.waiting_for_deadline)
async def process_new_deadline(message: Message, state: FSMContext):
    input_deadline = message.text.strip()
    try:
        new_deadline = datetime.strptime(input_deadline, "%d.%m.%Y - %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, укажите дату и время в формате: 01.01.2025 - 22:30")
        return

    await state.update_data(new_deadline=new_deadline)
    user_data = await state.get_data()
    manager_id = user_data.get('original_manager_id')
    executor_id = user_data.get('original_executor_id')
    result = await TaskService.create_new_task(
        manager_id=manager_id,
        executor_id=executor_id,
        title=user_data["new_title"],
        description=user_data["new_description"],
        deadline=new_deadline
    )

    if result['success']:
        original_task_id = user_data.get('original_task_id')
        if original_task_id:
            await TaskService.delete_task_for_task_id(original_task_id)
        await message.answer("Задача пересоздана!")
    else:
        await message.answer(f"Ошибка: {result['message']}")

    await state.clear()


@completed_tasks_router.message(F.text == "✅ Задача закрыта")
async def close_task(message: Message, state: FSMContext):
    user_data = await state.get_data()
    task_id = user_data.get('current_task_id')

    if task_id:
        await TaskService.delete_task_for_task_id(task_id)
        await message.answer(
            f"Вы закрыли задачу!\n"
            f"Задача считается выполненной, удалена из списка задач\n",
        )
    else:
        await message.answer("Ошибка: не удалось найти информацию о задаче.")

    await state.clear()
    await get_completed_task(message)


@completed_tasks_router.message(F.text == "📋 Вернуться к списку выполненных задач")
async def close_check_task(message: Message):
    await get_completed_task(message)


@completed_tasks_router.message(Command("completed_tasks"))
async def get_completed_task(message: Message):
    completed_tasks = await TaskService.get_completed_tasks()

    if not completed_tasks:
        await message.answer("Выполненных задач нет")
        return

    keyboard = build_completed_tasks_keyboard(completed_tasks)
    await message.answer("Выберите выполненную задачу для проверки:", reply_markup=keyboard)


@completed_tasks_router.callback_query(lambda c: c.data and c.data.startswith('select_completed_tasks:'))
async def get_completed_task_by_id(callback_query: CallbackQuery, state: FSMContext):
    task_id_str = callback_query.data.split(':')[1]
    task_id = int(task_id_str)

    await state.update_data(current_task_id=task_id)

    task = await TaskService.get_task_by_id_and_staff(task_id)
    if not task:
        await callback_query.message.answer("Ошибка: задача не найдена.")
        await callback_query.answer()
        return

    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    deadline_with_tz = task.deadline.replace(tzinfo=kemerovo_tz)
    completed_at_with_tz = task.completed_at.replace(tzinfo=kemerovo_tz)

    deadline_str = deadline_with_tz.strftime("%d.%m.%Y %H:%M")
    completed_at_str = completed_at_with_tz.strftime("%d.%m.%Y %H:%M")

    if task.executor:
        executor_info = f"{task.executor.full_name} - {task.executor.position}"
    else:
        executor_info = "Исполнитель не назначен"

    response_text = (
        f"«{task.title}»\n"
        f"Описание задачи: {task.description}\n"
        f"Дедлайн: {deadline_str}\n"
        f"\n"
        f"Сотрудник: {executor_info}\n"
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
        "❌ Доработать задачу - результат вас не устроил",
        reply_markup=chek_keyboard
    )
    await callback_query.answer()

