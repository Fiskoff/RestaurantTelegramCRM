from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app.keyboards.deadline_keyboars import create_deadline_keyboard, calculate_deadline_from_callback
from app.keyboards.change_task_keyboars import build_delete_tasks_keyboard, build_update_tasks_keyboard
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


@change_task_router.message(Command("change_task"))
async def get_change_task_keyboard(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить задачу", callback_data="action:update")],
        [InlineKeyboardButton(text="❌ Удалить задачу", callback_data="action:delete")]
    ])
    await message.answer("Изменение существующей задачи", reply_markup=keyboard)


@change_task_router.callback_query(lambda c: c.data and c.data.startswith('action:'))
async def process_main_action(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data.split(':')[1]

    if action == 'delete':
        tasks = await TaskService.get_all_task()
        if not tasks:
            await callback_query.message.edit_text("Нет задач для удаления")
            await callback_query.answer()
            return
        task_keyboard = build_delete_tasks_keyboard(tasks)
        await callback_query.message.edit_text("Выберите задачу для удаления:", reply_markup=task_keyboard)

    elif action == 'update':
        tasks = await TaskService.get_all_task()
        if not tasks:
            await callback_query.message.edit_text("Нет задач для изменения")
            await callback_query.answer()
            return
        task_keyboard = build_update_tasks_keyboard(tasks)
        await callback_query.message.edit_text("Выберите задачу для изменения:", reply_markup=task_keyboard)
        await state.set_state(UpdateTaskStates.waiting_for_field_choice)

    await callback_query.answer()


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

    field_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data="field:title")],
        [InlineKeyboardButton(text="📄 Описание", callback_data="field:description")],
        [InlineKeyboardButton(text="👤 Сотрудник", callback_data="field:executor")],
        [InlineKeyboardButton(text="⏰ Дедлайн", callback_data="field:deadline")],
        [InlineKeyboardButton(text="🏢 Назначить сектору", callback_data="field:sector_assignment")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="field:cancel")]
    ])

    await callback_query.message.answer("Что вы хотите изменить?", reply_markup=field_keyboard)
    await state.set_state(UpdateTaskStates.waiting_for_field_choice)
    await callback_query.answer()


@change_task_router.callback_query(UpdateTaskStates.waiting_for_field_choice,
                                   lambda c: c.data and c.data.startswith('field:'))
async def process_field_choice(callback_query: CallbackQuery, state: FSMContext):
    field = callback_query.data.split(':')[1]
    await state.update_data(field_to_update=field)

    if field == 'cancel':
        await callback_query.message.edit_text("Редактирование задачи отменено.")
        await state.clear()
        main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить задачу", callback_data="action:update")],
            [InlineKeyboardButton(text="❌ Удалить задачу", callback_data="action:delete")]
        ])
        await callback_query.message.answer("Изменение существующей задачи", reply_markup=main_keyboard)
        return
    elif field == 'sector_assignment':
        sector_keyboard = sector_selection_keyboard()
        await callback_query.message.edit_text("Выберите сектор, которому хотите назначить задачу:",
                                               reply_markup=sector_keyboard)
        await state.set_state(UpdateTaskStates.waiting_for_sector_choice)
    elif field == 'deadline':
        deadline_kb = create_deadline_keyboard()
        await callback_query.message.edit_text("Выберите новый срок выполнения задачи:", reply_markup=deadline_kb)
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
                await callback_query.message.edit_text(
                    f"Введите Telegram ID сотрудника для изменения:\n"
                    f"Список сотрудников:\n{employee_list}"
                )
            else:
                await callback_query.message.edit_text("Введите Telegram ID нового сотрудника:")
        else:
            field_name = field_names[field]
            await callback_query.message.edit_text(f"Введите новое {field_name}:")
        await state.set_state(UpdateTaskStates.waiting_for_new_value)

    await callback_query.answer()


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

        continue_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Продолжить редактирование", callback_data="continue:yes")],
            [InlineKeyboardButton(text="⏹️ Завершить", callback_data="continue:no")]
        ])

        await callback_query.message.answer(
            "Хотите изменить что-то еще в этой задаче?",
            reply_markup=continue_keyboard
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


def sector_selection_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🍸 Бар", callback_data="task_sector:bar_ch")],
        [InlineKeyboardButton(text="🍽️ Зал", callback_data="task_sector:hall_ch")],
        [InlineKeyboardButton(text="👨‍🍳 Кухня", callback_data="task_sector:kitchen_ch")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="task_sector:cancel_ch")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@change_task_router.callback_query(UpdateTaskStates.waiting_for_sector_choice)
async def process_sector_choice(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    task_id = user_data.get('task_id')

    if callback_query.data == "task_sector:cancel_ch":
        await callback_query.message.edit_text("Назначение сектору отменено.")
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

        field_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data="field:title")],
            [InlineKeyboardButton(text="📄 Описание", callback_data="field:description")],
            [InlineKeyboardButton(text="👤 Сотрудник", callback_data="field:executor")],
            [InlineKeyboardButton(text="⏰ Дедлайн", callback_data="field:deadline")],
            [InlineKeyboardButton(text="🏢 Назначить сектору", callback_data="field:sector_assignment")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="field:cancel")]
        ])

        await callback_query.message.edit_text(task_info + "\nЧто вы хотите изменить?", reply_markup=field_keyboard)
        await callback_query.answer()
        return

    sector_map = {
        "task_sector:bar_ch": SectorStatus.BAR,
        "task_sector:hall_ch": SectorStatus.HALL,
        "task_sector:kitchen_ch": SectorStatus.KITCHEN
    }

    sector = sector_map.get(callback_query.data)

    if not sector:
        await callback_query.answer("Ошибка при выборе сектора.", show_alert=True)
        return

    result = await TaskService.update_task_field(task_id, 'sector_task', sector)

    if result["success"]:
        updated_task = await TaskService.get_task_by_id(task_id)

        sector_names = {
            SectorStatus.BAR: "Бар",
            SectorStatus.HALL: "Зал",
            SectorStatus.KITCHEN: "Кухня"
        }
        sector_name = sector_names.get(sector, str(sector))

        deadline_str = format_deadline(updated_task.deadline)

        await callback_query.message.edit_text(
            f"Задача успешно переназначена!\n"
            f"Название: {updated_task.title}\n"
            f"Описание: {updated_task.description}\n"
            f"Исполнитель: Весь сектор ({sector_name})\n"
            f"Дедлайн: {deadline_str}\n"
        )

        continue_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Продолжить редактирование", callback_data="continue:yes")],
            [InlineKeyboardButton(text="⏹️ Завершить", callback_data="continue:no")]
        ])

        await callback_query.message.answer(
            "Хотите изменить что-то еще в этой задаче?",
            reply_markup=continue_keyboard
        )
        await state.set_state(UpdateTaskStates.waiting_for_continue)
    else:
        await callback_query.message.edit_text(f"Ошибка при переназначении задачи: {result['message']}")
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

            continue_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Продолжить редактирование", callback_data="continue:yes")],
                [InlineKeyboardButton(text="⏹️ Завершить", callback_data="continue:no")]
            ])

            await message.answer(
                "Хотите изменить что-то еще в этой задаче?",
                reply_markup=continue_keyboard
            )
            await state.set_state(UpdateTaskStates.waiting_for_continue)
        else:
            await message.answer(f"Ошибка при обновлении задачи: {result['message']}")
            await state.clear()

    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
        await state.clear()


@change_task_router.callback_query(UpdateTaskStates.waiting_for_continue)
async def process_continue_editing(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    task_id = user_data.get('task_id')

    if callback_query.data == "continue:yes":
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

        field_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data="field:title")],
            [InlineKeyboardButton(text="📄 Описание", callback_data="field:description")],
            [InlineKeyboardButton(text="👤 Сотрудник", callback_data="field:executor")],
            [InlineKeyboardButton(text="⏰ Дедлайн", callback_data="field:deadline")],
            [InlineKeyboardButton(text="🏢 Назначить сектору", callback_data="field:sector_assignment")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="field:cancel")]
        ])

        await callback_query.message.edit_text(task_info + "\nЧто вы хотите изменить?", reply_markup=field_keyboard)
        await state.set_state(UpdateTaskStates.waiting_for_field_choice)

    elif callback_query.data == "continue:no":
        await callback_query.message.edit_text("Редактирование задачи завершено.")
        main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить задачу", callback_data="action:update")],
            [InlineKeyboardButton(text="❌ Удалить задачу", callback_data="action:delete")]
        ])
        await callback_query.message.answer("Изменение существующей задачи", reply_markup=main_keyboard)
        await state.clear()

    await callback_query.answer()


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

    task_info = (
        f"Название: {selected_task.title}\n"
        f"Описание: {selected_task.description}\n"
        f"Исполнитель: {executor_info}\n"
        f"Дедлайн: {deadline_str}\n"
    )

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete:yes:{task_id}")],
        [InlineKeyboardButton(text="❌ Нет, отменить", callback_data="confirm_delete:no")]
    ])

    await callback_query.message.edit_text(task_info + "\nПодтвердите удаление задачи:", reply_markup=confirm_keyboard)
    await state.update_data(waiting_for_task_id=selected_task.task_id)
    await state.set_state(TaskDeleteUpdateStates.waiting_for_confirmation)


@change_task_router.callback_query(TaskDeleteUpdateStates.waiting_for_confirmation,
                                   lambda c: c.data and c.data.startswith('confirm_delete:'))
async def process_delete_task(callback_query: CallbackQuery, state: FSMContext):
    data_parts = callback_query.data.split(':')

    if data_parts[1] == "yes":
        task_id = int(data_parts[2])
        await TaskService.delete_task_for_task_id(task_id)
        await callback_query.message.edit_text("✅ Задача удалена")
        main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить задачу", callback_data="action:update")],
            [InlineKeyboardButton(text="❌ Удалить задачу", callback_data="action:delete")]
        ])
        await callback_query.message.answer("Изменение существующей задачи", reply_markup=main_keyboard)
    elif data_parts[1] == "no":
        await callback_query.message.edit_text("❌ Задача не была удалена")
        main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить задачу", callback_data="action:update")],
            [InlineKeyboardButton(text="❌ Удалить задачу", callback_data="action:delete")]
        ])
        await callback_query.message.answer("Изменение существующей задачи", reply_markup=main_keyboard)

    await state.clear()
    await callback_query.answer()