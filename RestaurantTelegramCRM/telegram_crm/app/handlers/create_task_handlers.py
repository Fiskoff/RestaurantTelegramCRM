from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.task_service import TaskService
from app.keyboards.create_task_keyboards import create_employee_selection_keyboard, create_sector_selection_keyboard
from core.models.base_model import SectorStatus
from app.keyboards.deadline_keyboars import create_deadline_keyboard, calculate_deadline_from_callback

create_task_router = Router()


class CreateTask(StatesGroup):
    waiting_for_assignment_type = State()
    waiting_for_executor_id = State()
    waiting_for_sector = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()


@create_task_router.message(Command("create_task"))
async def start_create_task(message: Message, state: FSMContext):
    manager_id = message.from_user.id
    await state.update_data(manager_id=manager_id)

    # Создаем инлайн клавиатуру для выбора типа назначения
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Конкретному сотруднику", callback_data="assignment:employee")],
        [InlineKeyboardButton(text="🏢 Всему сектору", callback_data="assignment:sector")],
        [InlineKeyboardButton(text="❌ Отменить создание задачи", callback_data="assignment:cancel")]
    ])

    await message.answer("Как вы хотите назначить задачу?", reply_markup=keyboard)
    await state.set_state(CreateTask.waiting_for_assignment_type)


@create_task_router.callback_query(lambda c: c.data and c.data.startswith('assignment:'))
async def process_assignment_type(callback_query: CallbackQuery, state: FSMContext):
    assignment_type = callback_query.data.split(':')[1]

    if assignment_type == "employee":
        keyboard = await create_employee_selection_keyboard()
        await callback_query.message.edit_text("Выберите сотрудника, которому хотите назначить задачу:",
                                               reply_markup=keyboard)
        await state.set_state(CreateTask.waiting_for_executor_id)
    elif assignment_type == "sector":
        # Создаем инлайн клавиатуру для выбора сектора
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍸 Бар", callback_data="select_sector:bar")],
            [InlineKeyboardButton(text="🍽️ Зал", callback_data="select_sector:hall")],
            [InlineKeyboardButton(text="‍👨‍🍳 Кухня", callback_data="select_sector:kitchen")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="select_sector:cancel")]
        ])

        await callback_query.message.edit_text("Выберите сектор, которому хотите назначить задачу:",
                                               reply_markup=keyboard)
        await state.set_state(CreateTask.waiting_for_sector)
    elif assignment_type == "cancel":
        await callback_query.message.edit_text("Создание задачи отменено!")
        await state.clear()

    await callback_query.answer()


# Удаляем этот хендлер, так как теперь используем callback
# @create_task_router.message(CreateTask.waiting_for_assignment_type)
# async def process_assignment_type(message: Message, state: FSMContext):
#     # ... старый код ...


@create_task_router.callback_query(lambda c: c.data and c.data.startswith('select_employee:'))
async def process_employee_selection(callback_query: CallbackQuery, state: FSMContext):
    try:
        executor_id_str = callback_query.data.split(':')[1]
        executor_id = int(executor_id_str)
    except (IndexError, ValueError):
        await callback_query.answer("Ошибка при обработке выбора сотрудника.", show_alert=True)
        return

    await state.update_data(executor_id=executor_id)
    await state.update_data(sector_task=None)
    await callback_query.answer()
    await callback_query.message.edit_text("Напишите название задачи")
    await state.set_state(CreateTask.waiting_for_title)


@create_task_router.callback_query(lambda c: c.data and c.data.startswith('select_sector:'))
async def process_sector_selection(callback_query: CallbackQuery, state: FSMContext):
    try:
        sector_str = callback_query.data.split(':')[1]

        # Проверяем, если пользователь выбрал отмену
        if sector_str == "cancel":
            await callback_query.message.edit_text("Создание задачи отменено!")
            await state.clear()
            await callback_query.answer()
            return

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
        await state.update_data(executor_id=None)
        await callback_query.answer()
        await callback_query.message.edit_text("Напишите название задачи")
        await state.set_state(CreateTask.waiting_for_title)
    except (IndexError, ValueError):
        await callback_query.answer("Ошибка при обработке выбора сектора.", show_alert=True)
        return


# Удаляем этот хендлер, так как теперь используем callback
# @create_task_router.message(CreateTask.waiting_for_executor_id)
# async def process_executor(message: Message, state: FSMContext):
#     # ... старый код ...


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

    keyboard = create_deadline_keyboard()
    await message.answer("Выберите срок выполнения задачи:", reply_markup=keyboard)
    await state.set_state(CreateTask.waiting_for_deadline)


@create_task_router.callback_query(StateFilter(CreateTask.waiting_for_deadline))
async def process_deadline_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    data = callback_query.data
    user_id = callback_query.from_user.id

    if data == "deadline:manual":
        await callback_query.message.edit_text(
            "Укажите дату и время окончания задачи в формате: 01.01.2025 - 22:30"
        )
        return

    deadline_dt = calculate_deadline_from_callback(data)

    if data == "deadline:never":
        await state.update_data(deadline=None)
        await callback_query.message.edit_text("Выбран срок: Бессрочно")
    elif deadline_dt:
        await state.update_data(deadline=deadline_dt)
        await callback_query.message.edit_text(
            f"Выбран срок: {deadline_dt.strftime('%d.%m.%Y - %H:%M')}")
    else:
        await callback_query.message.edit_text("Ошибка при выборе срока. Попробуйте снова.")
        return

    task_data = await state.get_data()

    manager_id = task_data["manager_id"]
    executor_id = task_data.get("executor_id")
    sector_task = task_data.get("sector_task")
    title = task_data["title"]
    description = task_data["description"]

    result = await TaskService.create_new_task(
        manager_id=manager_id,
        executor_id=executor_id,
        title=title,
        description=description,
        deadline=deadline_dt,
        sector_task=sector_task
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
            await callback_query.message.answer(f"Задача создана и назначена сектору: {sector_name}!")
        else:
            await callback_query.message.answer("Задача создана и назначена сотруднику!")
    else:
        await callback_query.message.answer(f"Ошибка: {result['message']}")


@create_task_router.message(StateFilter(CreateTask.waiting_for_deadline))
async def process_deadline_manual(message: Message, state: FSMContext):
    deadline_str = message.text.strip()

    try:
        deadline_dt = datetime.strptime(deadline_str, "%d.%m.%Y - %H:%M")
        from zoneinfo import ZoneInfo
        kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        deadline_dt = deadline_dt.replace(tzinfo=kemerovo_tz)
        await state.update_data(deadline=deadline_dt)

    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, укажите дату и время в формате: 01.01.2025 - 22:30")
        return

    task_data = await state.get_data()

    manager_id = task_data["manager_id"]
    executor_id = task_data.get("executor_id")
    sector_task = task_data.get("sector_task")
    title = task_data["title"]
    description = task_data["description"]

    result = await TaskService.create_new_task(
        manager_id=manager_id,
        executor_id=executor_id,
        title=title,
        description=description,
        deadline=deadline_dt,
        sector_task=sector_task
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