from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.task_service import TaskService
from core.models.base_model import UserRole


task_router = Router()


class CreateTask(StatesGroup):
    waiting_for_executor_id = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()


@task_router.message(Command("create_task"))
async def start_create_task(message: Message, state: FSMContext):
    await state.update_data(manager_id=message.from_user.id)
    await message.answer("Выберите сотрудника которому вы хотите назначить задачу. Укажите его id")
    await state.set_state(CreateTask.waiting_for_executor_id)


@task_router.message(CreateTask.waiting_for_executor_id)
async def process_full_name(message: Message, state: FSMContext):
    executor_id = message.text.strip()
    await state.update_data(executor_id=executor_id)
    await message.answer("Напишите название задачи")
    await state.set_state(CreateTask.waiting_for_title)


@task_router.message(CreateTask.waiting_for_title)
async def process_full_name(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await message.answer("Подробно опишите, что нужно сделать?")
    await state.set_state(CreateTask.waiting_for_description)


@task_router.message(CreateTask.waiting_for_description)
async def process_full_name(message: Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)
    await message.answer("Укажите дату и время окончания задачи")
    await state.set_state(CreateTask.waiting_for_deadline)


@task_router.message(CreateTask.waiting_for_deadline)
async def process_full_name(message: Message, state: FSMContext):
    deadline = message.text.strip()
    await state.update_data(deadline=deadline)

    data = await state.get_data()
    result = await TaskService.create_new_task(
        manager_id=data["manager_id"],
        executor_id=data["executor_id"],
        title=data["title"],
        description=data["description"],
        deadline=data["deadline"]
    )
    await state.clear()

    if result['success']:
        await message.answer(f"Задача создана!")
    else:
        await message.answer(f"Ошибка: {result['message']}")