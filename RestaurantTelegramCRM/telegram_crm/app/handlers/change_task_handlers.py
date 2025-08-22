from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from app.keyboards.deadline_keyboars import create_deadline_keyboard, calculate_deadline_from_callback

from app.keyboards.change_task_keyboars import build_delete_tasks_keyboard, build_update_tasks_keyboard
from app.keyboards.task_reply_keyboard import get_update_task_action_keyboard
from app.services.task_service import TaskService
from app.services.user_service import UserService
from core.models import SectorStatus

change_task_router = Router()


class TaskDeleteUpdateStates(StatesGroup):
    waiting_for_task_id = State()
    waiting_for_confirmation = State()


class UpdateTaskStates(StatesGroup):
    waiting_for_field_choice = State()
    waiting_for_new_value = State()
    waiting_for_continue = State()
    waiting_for_sector_choice = State()


def format_deadline(deadline: datetime | None) -> str:
    if deadline is None:
        return "Бессрочно"

    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    if deadline.tzinfo is None:
        deadline_with_tz = deadline.replace(tzinfo=kemerovo_tz)
    else:
        deadline_with_tz = deadline.astimezone(kemerovo_tz)

    return deadline_with_tz.strftime('%d.%m.%Y - %H:%M')


@change_task_router.message(F.text == "❌ Удалить задачу")
async def delete_task(message: Message):
    tasks = await TaskService.get_all_task()
    task_keyboard = build_delete_tasks_keyboard(tasks)
    await message.answer("Выберите задачу для удаления:", reply_markup=task_keyboard)


@change_task_router.message(F.text == "✏️ Изменить задачу")
async def change_task(message: Message, state: FSMContext):
    tasks = await TaskService.get_all_task()
    if not tasks:
        await message.answer("Нет задач для изменения")
        return
    task_keyboard = build_update_tasks_keyboard(tasks)
    await message.answer("Выберите задачу для изменения:", reply_markup=task_keyboard)
    await state.set_state(UpdateTaskStates.waiting_for_field_choice)


@change_task_router.callback_query(lambda c: c.data and c.data.startswith('update_task:'))
async def start_change_task(callback_query: CallbackQuery, state: FSMContext):
    task_id_str = callback_query.data.split(':')[1]
    task_id = int(task_id_str)
    selected_task = await TaskService.get_task_by_id(task_id)

    await state.update_data(task_id=task_id)

    if selected_task.executor:
        executor_info = f"{selected_task.executor.full_name} - {selected_task.executor.position}"
    else:
        if selected_task.sector_task:
            sector_names = {
                SectorStatus.BAR: "Бар",
                SectorStatus.HALL: "Зал",
                SectorStatus.KITCHEN: "Кухня"
            }
            sector_name = sector_names.get(selected_task.sector_task, str(selected_task.sector_task))
            executor_info = f"Весь сектор ({sector_name})"
        else:
            executor_info = "Исполнитель не назначен"

    deadline_str = format_deadline(selected_task.deadline)

    task_info = (
        f"Задача для изменения:\n"
        f"Название: {selected_task.title}\n"
        f"Описание: {selected_task.description}\n"
        f"Исполнитель: {executor_info}\n"
        f"Дедлайн: {deadline_str}\n"
    )

    await callback_query.message.answer(task_info)
    await callback_query.message.answer(
        "Что вы хотите изменить?\n"
        "1 - Название\n"
        "2 - Описание\n"
        "3 - Сотрудник\n"
        "4 - Дедлайн\n"
        "5 - Назначить сектору (снять с сотрудника)\n"
        "6 - Отмена\n"
        "Отправьте подходящее число"
    )
    await state.set_state(UpdateTaskStates.waiting_for_field_choice)
    await callback_query.answer()


@change_task_router.message(UpdateTaskStates.waiting_for_field_choice)
async def process_field_choice(message: Message, state: FSMContext):
    field_map = {
        '1': 'title',
        '2': 'description',
        '3': 'executor',
        '4': 'deadline',
        '5': 'sector_assignment',
        '6': 'cancel'
    }

    if message.text not in field_map:
        await message.answer("Пожалуйста, введите число от 1 до 6")
        return

    field = field_map[message.text]
    await state.update_data(field_to_update=field)

    if field == 'cancel':
        await message.answer("Редактирование задачи отменено.")
        await state.clear()
        await show_all_tasks(message)
        return
    elif field == 'sector_assignment':
        sector_keyboard = create_sector_selection_keyboard()
        await message.answer("Выберите сектор, которому хотите назначить задачу:", reply_markup=sector_keyboard)
        await state.set_state(UpdateTaskStates.waiting_for_sector_choice)
    elif field == 'deadline':
        deadline_kb = create_deadline_keyboard()
        await message.answer("Выберите новый срок выполнения задачи:", reply_markup=deadline_kb)
        await state.set_state(UpdateTaskStates.waiting_for_new_value)
    else:
        field_names = {
            'title': 'название задачи',
            'description': 'описание задачи',
            'executor': 'сотрудника (введите Telegram ID)',
        }

        if field == 'executor':
            employees = await UserService.get_all_users()
            if employees:
                employee_list = "\n".join([
                    f"{emp.telegram_id} - {emp.full_name} ({emp.position})"
                    for emp in employees
                ])
                await message.answer(
                    f"Введите Telegram ID сотрудника для изменения:\n"
                    f"Список сотрудников:\n{employee_list}"
                )
            else:
                await message.answer("Введите Telegram ID нового сотрудника:")
        else:
            field_name = field_names[field]
            await message.answer(f"Введите новое {field_name}:")
        await state.set_state(UpdateTaskStates.waiting_for_new_value)


@change_task_router.callback_query(StateFilter(UpdateTaskStates.waiting_for_new_value),
                                   lambda c: c.data and c.data.startswith('deadline:'))
async def process_deadline_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()
    task_id = user_data.get('task_id')
    field_to_update = user_data.get('field_to_update')

    if not task_id or field_to_update != 'deadline':
        await callback_query.message.answer("Произошла ошибка. Попробуйте начать сначала.")
        await state.clear()
        return

    data = callback_query.data

    if data == "deadline:manual":
        await callback_query.message.edit_text(
            "Укажите новую дату и время окончания задачи в формате: 01.01.2025 - 22:30"
        )
        return

    new_deadline = calculate_deadline_from_callback(data)

    result = await TaskService.update_task_field(task_id, 'deadline', new_deadline)

    if result["success"]:
        updated_task = await TaskService.get_task_by_id(task_id)

        if updated_task.executor:
            executor_info = f"{updated_task.executor.full_name} - {updated_task.executor.position}"
        else:
            if updated_task.sector_task:
                sector_names = {
                    SectorStatus.BAR: "Бар",
                    SectorStatus.HALL: "Зал",
                    SectorStatus.KITCHEN: "Кухня"
                }
                sector_name = sector_names.get(updated_task.sector_task, str(updated_task.sector_task))
                executor_info = f"Весь сектор ({sector_name})"
            else:
                executor_info = "Исполнитель не назначен"

        deadline_str = format_deadline(updated_task.deadline)

        await callback_query.message.edit_text(
            f"Задача успешно обновлена!\n"
            f"Название: {updated_task.title}\n"
            f"Описание: {updated_task.description}\n"
            f"Исполнитель: {executor_info}\n"
            f"Дедлайн: {deadline_str}\n"
        )

        await callback_query.message.answer(
            "Хотите изменить что-то еще в этой задаче?\n"
            "Введите 'да' для продолжения или 'нет' для завершения"
        )
        await state.set_state(UpdateTaskStates.waiting_for_continue)
    else:
        await callback_query.message.edit_text(f"Ошибка при обновлении задачи: {result['message']}")
        await state.clear()


async def show_all_tasks(message: Message):
    tasks = await TaskService.get_all_task()
    if not tasks:
        await message.answer("Нет задач для изменения")
        return

    task_keyboard = build_update_tasks_keyboard(tasks)
    await message.answer("Выберите задачу для изменения:", reply_markup=task_keyboard)


def create_sector_selection_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = [
        [InlineKeyboardButton(text="🍸 Бар", callback_data="sector:bar")],
        [InlineKeyboardButton(text="🍽️ Зал", callback_data="sector:hall")],
        [InlineKeyboardButton(text="👨‍🍳 Кухня", callback_data="sector:kitchen")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="sector:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@change_task_router.callback_query(UpdateTaskStates.waiting_for_sector_choice)
async def process_sector_choice(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    task_id = user_data.get('task_id')

    if callback_query.data == "sector:cancel":
        await callback_query.message.answer("Назначение сектору отменено.")
        await state.set_state(UpdateTaskStates.waiting_for_field_choice)
        selected_task = await TaskService.get_task_by_id(task_id)

        if selected_task.executor:
            executor_info = f"{selected_task.executor.full_name} - {selected_task.executor.position}"
        else:
            if selected_task.sector_task:
                sector_names = {
                    SectorStatus.BAR: "Бар",
                    SectorStatus.HALL: "Зал",
                    SectorStatus.KITCHEN: "Кухня"
                }
                sector_name = sector_names.get(selected_task.sector_task, str(selected_task.sector_task))
                executor_info = f"Весь сектор ({sector_name})"
            else:
                executor_info = "Исполнитель не назначен"

        deadline_str = format_deadline(selected_task.deadline)

        task_info = (
            f"Задача для изменения:\n"
            f"Название: {selected_task.title}\n"
            f"Описание: {selected_task.description}\n"
            f"Исполнитель: {executor_info}\n"
            f"Дедлайн: {deadline_str}\n"
        )

        await callback_query.message.answer(task_info)
        await callback_query.message.answer(
            "Что вы хотите изменить?\n"
            "1 - Название\n"
            "2 - Описание\n"
            "3 - Сотрудник\n"
            "4 - Дедлайн\n"
            "5 - Назначить сектору (снять с сотрудника)\n"
            "6 - Отмена\n"
            "Отправьте подходящее число"
        )
        await callback_query.answer()
        return

    sector_map = {
        "sector:bar": SectorStatus.BAR,
        "sector:hall": SectorStatus.HALL,
        "sector:kitchen": SectorStatus.KITCHEN
    }

    sector = sector_map.get(callback_query.data)

    if not sector:
        await callback_query.answer("Ошибка при выборе сектора.", show_alert=True)
        return

    result = await TaskService.update_task_field(task_id, 'sector_task', sector)  # Передаем Enum

    if result["success"]:
        updated_task = await TaskService.get_task_by_id(task_id)

        sector_names = {
            SectorStatus.BAR: "Бар",
            SectorStatus.HALL: "Зал",
            SectorStatus.KITCHEN: "Кухня"
        }
        sector_name = sector_names.get(sector, str(sector))

        deadline_str = format_deadline(updated_task.deadline)

        await callback_query.message.answer(
            f"Задача успешно переназначена!\n"
            f"Название: {updated_task.title}\n"
            f"Описание: {updated_task.description}\n"
            f"Исполнитель: Весь сектор ({sector_name})\n"
            f"Дедлайн: {deadline_str}\n"
        )

        await callback_query.message.answer(
            "Хотите изменить что-то еще в этой задаче?\n"
            "Введите 'да' для продолжения или 'нет' для завершения"
        )
        await state.set_state(UpdateTaskStates.waiting_for_continue)
    else:
        await callback_query.message.answer(f"Ошибка при переназначении задачи: {result['message']}")
        await state.clear()

    await callback_query.answer()


@change_task_router.message(UpdateTaskStates.waiting_for_new_value)
async def process_new_value(message: Message, state: FSMContext):
    user_data = await state.get_data()
    task_id = user_data.get('task_id')
    field_to_update = user_data.get('field_to_update')

    if not task_id or not field_to_update:
        await message.answer("Произошла ошибка. Попробуйте начать сначала.")
        await state.clear()
        return

    try:
        new_value = message.text

        if field_to_update == 'title':
            if len(new_value.strip()) == 0:
                await message.answer("Название не может быть пустым")
                return
        elif field_to_update == 'executor':
            try:
                new_value = int(new_value)
                employee = await UserService.get_user_by_telegram_id(new_value)
                if not employee:
                    await message.answer("Сотрудник с таким Telegram ID не найден")
                    return
                await TaskService.update_task_field(task_id, 'sector_task', None)
            except ValueError:
                await message.answer("Введите корректный Telegram ID (число)")
                return
        elif field_to_update == 'deadline':
            try:
                deadline_dt = datetime.strptime(new_value, "%d.%m.%Y - %H:%M")
                kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
                new_value = deadline_dt.replace(tzinfo=kemerovo_tz)
            except ValueError:
                await message.answer("Введите дату в формате 01.01.2025 - 22:30")
                return
        else:
            pass

        result = await TaskService.update_task_field(task_id, field_to_update, new_value)

        if result["success"]:
            updated_task = await TaskService.get_task_by_id(task_id)

            if updated_task.executor:
                executor_info = f"{updated_task.executor.full_name} - {updated_task.executor.position}"
            else:
                if updated_task.sector_task:
                    sector_names = {
                        SectorStatus.BAR: "Бар",
                        SectorStatus.HALL: "Зал",
                        SectorStatus.KITCHEN: "Кухня"
                    }
                    sector_name = sector_names.get(updated_task.sector_task, str(updated_task.sector_task))
                    executor_info = f"Весь сектор ({sector_name})"
                else:
                    executor_info = "Исполнитель не назначен"

            deadline_str = format_deadline(updated_task.deadline)

            await message.answer(
                f"Задача успешно обновлена!\n"
                f"Название: {updated_task.title}\n"
                f"Описание: {updated_task.description}\n"
                f"Исполнитель: {executor_info}\n"
                f"Дедлайн: {deadline_str}\n"
            )

            await message.answer(
                "Хотите изменить что-то еще в этой задаче?\n"
                "Введите 'да' для продолжения или 'нет' для завершения"
            )
            await state.set_state(UpdateTaskStates.waiting_for_continue)
        else:
            await message.answer(f"Ошибка при обновлении задачи: {result['message']}")
            await state.clear()

    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
        await state.clear()


@change_task_router.message(UpdateTaskStates.waiting_for_continue)
async def process_continue_editing(message: Message, state: FSMContext):
    user_data = await state.get_data()
    task_id = user_data.get('task_id')

    if message.text.lower() in ['да', 'yes', 'y']:
        selected_task = await TaskService.get_task_by_id(task_id)

        if selected_task.executor:
            executor_info = f"{selected_task.executor.full_name} - {selected_task.executor.position}"
        else:
            if selected_task.sector_task:
                sector_names = {
                    SectorStatus.BAR: "Бар",
                    SectorStatus.HALL: "Зал",
                    SectorStatus.KITCHEN: "Кухня"
                }
                sector_name = sector_names.get(selected_task.sector_task, str(selected_task.sector_task))
                executor_info = f"Весь сектор ({sector_name})"
            else:
                executor_info = "Исполнитель не назначен"

        deadline_str = format_deadline(selected_task.deadline)

        task_info = (
            f"Задача для изменения:\n"
            f"Название: {selected_task.title}\n"
            f"Описание: {selected_task.description}\n"
            f"Исполнитель: {executor_info}\n"
            f"Дедлайн: {deadline_str}\n"
        )

        await message.answer(task_info)
        await message.answer(
            "Что вы хотите изменить?\n"
            "1 - Название\n"
            "2 - Описание\n"
            "3 - Сотрудник\n"
            "4 - Дедлайн\n"
            "5 - Назначить сектору (снять с сотрудника)\n"
            "6 - Отмена\n"
            "Отправьте подходящее число"
        )
        await state.set_state(UpdateTaskStates.waiting_for_field_choice)

    elif message.text.lower() in ['нет', 'no', 'n']:
        await message.answer("Редактирование задачи завершено.")
        await state.clear()
    else:
        await message.answer(
            "Пожалуйста, введите 'да' для продолжения редактирования или 'нет' для завершения"
        )


@change_task_router.callback_query(lambda c: c.data and c.data.startswith('delete_task:'))
async def start_delete_task(callback_query: CallbackQuery, state: FSMContext):
    task_id_str = callback_query.data.split(':')[1]
    task_id = int(task_id_str)
    selected_task = await TaskService.get_task_by_id(task_id)

    if selected_task.executor:
        executor_info = f"{selected_task.executor.full_name} - {selected_task.executor.position}"
    else:
        if selected_task.sector_task:
            sector_names = {
                SectorStatus.BAR: "Бар",
                SectorStatus.HALL: "Зал",
                SectorStatus.KITCHEN: "Кухня"
            }
            sector_name = sector_names.get(selected_task.sector_task, str(selected_task.sector_task))
            executor_info = f"Весь сектор ({sector_name})"
        else:
            executor_info = "Исполнитель не назначен"

    deadline_str = format_deadline(selected_task.deadline)

    await callback_query.message.answer(
        f"Название: {selected_task.title}\n"
        f"Описание: {selected_task.description}\n"
        f"Исполнитель: {executor_info}\n"
        f"Дедлайн: {deadline_str}\n"
    )
    await callback_query.message.answer(
        "Подтвердите удаление задачи\n"
        "Отправите:\n"
        "да - если уверены\n"
        "нет - если хотите отменить удаление"
    )
    await state.update_data(waiting_for_task_id=selected_task.task_id)
    await state.set_state(TaskDeleteUpdateStates.waiting_for_confirmation)


@change_task_router.message(TaskDeleteUpdateStates.waiting_for_confirmation)
async def process_delete_task(message: Message, state: FSMContext):
    task_date = await state.get_data()
    delete_task_id = task_date.get('waiting_for_task_id')
    waiting_for_confirmation = message.text

    if waiting_for_confirmation == "да":
        await TaskService.delete_task_for_task_id(delete_task_id)
        await message.answer("Задача удалена")
        await get_change_task_keyboard(message)
    elif waiting_for_confirmation == "нет":
        await message.answer("Задача не была удалена")
    else:
        await message.answer(
            "Ошибка ввода\n"
            "Отправите:\n"
            "да - если уверены\n"
            "нет - если хотите отменить удаление"
        )
    await state.clear()


@change_task_router.message(Command("change_task"))
async def get_change_task_keyboard(message: Message):
    keyboard = get_update_task_action_keyboard()
    await message.answer("Изменение существующей задачи", reply_markup=keyboard)