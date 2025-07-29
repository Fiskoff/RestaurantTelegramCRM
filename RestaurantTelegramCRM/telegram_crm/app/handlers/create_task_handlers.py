from datetime import datetime

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.task_service import TaskService
from app.keyboards.create_task_keyboards import create_employee_selection_keyboard


create_task_router = Router()


class CreateTask(StatesGroup):
    waiting_for_executor_id = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()


@task_router.message(Command("create_task"))
async def start_create_task(message: Message, state: FSMContext):
    manager_id = message.from_user.id
    await state.update_data(manager_id=manager_id)

    keyboard = await create_employee_selection_keyboard()
    await message.answer("Выберите сотрудника, которому хотите назначить задачу:", reply_markup=keyboard)


@task_router.callback_query(lambda c: c.data and c.data.startswith('select_employee:'))
async def process_employee_selection(callback_query: CallbackQuery, state: FSMContext):
    try:
        executor_id_str = callback_query.data.split(':')[1]
        executor_id = int(executor_id_str)
    except (IndexError, ValueError):
        await callback_query.answer("Ошибка при обработке выбора сотрудника.", show_alert=True)
        return

    await state.update_data(executor_id=executor_id)
    await callback_query.answer()
    await callback_query.message.answer("Напишите название задачи", reply_markup=None)
    await state.set_state(CreateTask.waiting_for_title)


@task_router.message(CreateTask.waiting_for_executor_id)
async def process_executor(message: Message, state: FSMContext):
    executor_id = message.text.strip()
    await state.update_data(executor_id=executor_id)
    await message.answer("Напишите название задачи")
    await state.set_state(CreateTask.waiting_for_title)


@task_router.message(CreateTask.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await message.answer("Подробно опишите, что нужно сделать?")
    await state.set_state(CreateTask.waiting_for_description)


@task_router.message(CreateTask.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)
    await message.answer("Укажите дату и время окончания задачи \nВ формате: 01.01.2025 - 22:30")
    await state.set_state(CreateTask.waiting_for_deadline)


@task_router.message(CreateTask.waiting_for_deadline)
async def process_deadline(message: Message, state: FSMContext):
    deadline = message.text.strip()

    try:
        deadline_dt = datetime.strptime(deadline, "%d.%m.%Y - %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, укажите дату и время в формате: 01.01.2025 - 22:30")
        return

    await state.update_data(deadline=deadline_dt)
    data = await state.get_data()

    result = await TaskService.create_new_task(
        manager_id=data["manager_id"],
        executor_id=data["executor_id"],
        title=data["title"],
        description=data["description"],
        deadline=deadline_dt
    )
    await state.clear()

    if result['success']:
        await message.answer("Задача создана!")
    else:
        await message.answer(f"Ошибка: {result['message']}")