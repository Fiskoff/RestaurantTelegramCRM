from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.task_service import TaskService
from app.keyboards.create_task_keyboards import create_employee_selection_keyboard, create_sector_selection_keyboard
from core.models.base_model import SectorStatus


create_task_router = Router()


class CreateTask(StatesGroup):
    waiting_for_assignment_type = State()  # Новый стейт для выбора типа назначения
    waiting_for_executor_id = State()
    waiting_for_sector = State()  # Новый стейт для выбора сектора
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()


@create_task_router.message(Command("create_task"))
async def start_create_task(message: Message, state: FSMContext):
    manager_id = message.from_user.id
    await state.update_data(manager_id=manager_id)

    # Предлагаем выбрать тип назначения задачи
    await message.answer(
        "Как вы хотите назначить задачу?\n"
        "1 - Конкретному сотруднику\n"
        "2 - Всему сектору"
    )
    await state.set_state(CreateTask.waiting_for_assignment_type)


@create_task_router.message(CreateTask.waiting_for_assignment_type)
async def process_assignment_type(message: Message, state: FSMContext):
    if message.text == "1":
        # Назначение конкретному сотруднику
        keyboard = await create_employee_selection_keyboard()
        await message.answer("Выберите сотрудника, которому хотите назначить задачу:", reply_markup=keyboard)
        await state.set_state(CreateTask.waiting_for_executor_id)
    elif message.text == "2":
        # Назначение всему сектору
        keyboard = create_sector_selection_keyboard()
        await message.answer("Выберите сектор, которому хотите назначить задачу:", reply_markup=keyboard)
        await state.set_state(CreateTask.waiting_for_sector)
    else:
        await message.answer(
            "Пожалуйста, выберите тип назначения:\n"
            "1 - Конкретному сотруднику\n"
            "2 - Всему сектору"
        )


@create_task_router.callback_query(lambda c: c.data and c.data.startswith('select_employee:'))
async def process_employee_selection(callback_query: CallbackQuery, state: FSMContext):
    try:
        executor_id_str = callback_query.data.split(':')[1]
        executor_id = int(executor_id_str)
    except (IndexError, ValueError):
        await callback_query.answer("Ошибка при обработке выбора сотрудника.", show_alert=True)
        return

    await state.update_data(executor_id=executor_id)
    await state.update_data(sector_task=None)  # Явно указываем, что сектор не выбран
    await callback_query.answer()
    await callback_query.message.answer("Напишите название задачи")
    await state.set_state(CreateTask.waiting_for_title)


@create_task_router.callback_query(lambda c: c.data and c.data.startswith('select_sector:'))
async def process_sector_selection(callback_query: CallbackQuery, state: FSMContext):
    try:
        sector_str = callback_query.data.split(':')[1]
        # Преобразуем строку в значение Enum
        sector_map = {
            "bar": SectorStatus.BAR,
            "hall": SectorStatus.HALL,
            "kitchen": SectorStatus.KITCHEN
        }
        sector = sector_map.get(sector_str)

        if not sector:
            await callback_query.answer("Ошибка при обработке выбора сектора.", show_alert=True)
            return

        await state.update_data(sector_task=sector)
        await state.update_data(executor_id=None)  # Явно указываем, что сотрудник не выбран
        await callback_query.answer()
        await callback_query.message.answer("Напишите название задачи")
        await state.set_state(CreateTask.waiting_for_title)
    except (IndexError, ValueError):
        await callback_query.answer("Ошибка при обработке выбора сектора.", show_alert=True)
        return


@create_task_router.message(CreateTask.waiting_for_executor_id)
async def process_executor(message: Message, state: FSMContext):
    executor_id = message.text.strip()
    await state.update_data(executor_id=executor_id)
    await state.update_data(sector_task=None)  # Явно указываем, что сектор не выбран
    await message.answer("Напишите название задачи")
    await state.set_state(CreateTask.waiting_for_title)


@create_task_router.message(CreateTask.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await message.answer("Подробно опишите, что нужно сделать?")
    await state.set_state(CreateTask.waiting_for_description)


@create_task_router.message(CreateTask.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)
    await message.answer("Укажите дату и время окончания задачи \nВ формате: 01.01.2025 - 22:30")
    await state.set_state(CreateTask.waiting_for_deadline)


@create_task_router.message(CreateTask.waiting_for_deadline)
async def process_deadline(message: Message, state: FSMContext):
    deadline = message.text.strip()

    try:
        deadline_dt = datetime.strptime(deadline, "%d.%m.%Y - %H:%M")
        # Добавляем временную зону
        kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        deadline_dt = deadline_dt.replace(tzinfo=kemerovo_tz)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, укажите дату и время в формате: 01.01.2025 - 22:30")
        return

    await state.update_data(deadline=deadline_dt)
    data = await state.get_data()

    # Определяем параметры для создания задачи
    manager_id = data["manager_id"]
    executor_id = data.get("executor_id")
    sector_task = data.get("sector_task")
    title = data["title"]
    description = data["description"]

    result = await TaskService.create_new_task(
        manager_id=manager_id,
        executor_id=executor_id,
        title=title,
        description=description,
        deadline=deadline_dt,
        sector_task=sector_task  # Передаем сектор, если задача для сектора
    )

    await state.clear()

    if result['success']:
        if sector_task:
            sector_names = {
                SectorStatus.BAR: "бар",
                SectorStatus.HALL: "зал",
                SectorStatus.KITCHEN: "кухня"
            }
            sector_name = sector_names.get(sector_task, "неизвестный сектор")
            await message.answer(f"Задача создана и назначена сектору: {sector_name}!")
        else:
            await message.answer("Задача создана и назначена сотруднику!")
    else:
        await message.answer(f"Ошибка: {result['message']}")