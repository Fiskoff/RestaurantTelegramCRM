from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from app.keyboards.delete_task_keyboars import build_delete_tasks_keyboard, build_update_tasks_keyboard
from app.keyboards.task_reply_keyboard import get_update_task_action_keyboard
from app.services.task_service import TaskService
from app.services.user_service import UserService


change_task_router = Router()


class TaskDeleteUpdateStates(StatesGroup):
    waiting_for_task_id = State()
    waiting_for_confirmation = State()


class UpdateTaskStates(StatesGroup):
    waiting_for_field_choice = State()
    waiting_for_new_value = State()
    waiting_for_continue = State()


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

    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    deadline_with_tz = selected_task.deadline.replace(tzinfo=kemerovo_tz)

    await state.update_data(task_id=task_id)

    task_info = (
        f"Задача для изменения:\n\n"
        f"Название: {selected_task.title}\n"
        f"Описание: {selected_task.description}\n"
        f"Сотрудник: {selected_task.executor.full_name} - {selected_task.executor.position}\n"
        f"Дедлайн: {deadline_with_tz.strftime('%d.%m.%Y - %H:%M')}\n"
    )

    await callback_query.message.answer(task_info)
    await callback_query.message.answer(
        "Что вы хотите изменить?\n"
        "1 - Название\n"
        "2 - Описание\n"
        "3 - Сотрудник\n"
        "4 - Дедлайн\n"
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
        '4': 'deadline'
    }

    if message.text not in field_map:
        await message.answer("Пожалуйста, введите число от 1 до 4")
        return

    field = field_map[message.text]
    await state.update_data(field_to_update=field)

    field_names = {
        'title': 'название задачи',
        'description': 'описание задачи',
        'executor': 'сотрудника (введите Telegram ID)',
        'deadline': 'дедлайн (в формате 01.01.2025 - 22:30)'
    }

    if field == 'executor':
        employees = await UserService.get_all_users()
        if employees:
            employee_list = "\n".join([
                f"{emp.telegram_id} - {emp.full_name} ({emp.position})"
                for emp in employees
            ])
            await message.answer(
                f"Введите Telegram ID сотрудника для изменения:\n\n"
                f"Список сотрудников:\n{employee_list}"
            )
        else:
            await message.answer("Введите Telegram ID нового сотрудника:")
    elif field == 'deadline':
        await message.answer("Введите новую дату дедлайна в формате 01.01.2025 - 22:30")
    else:
        field_name = field_names[field]
        await message.answer(f"Введите новое {field_name}:")

    await state.set_state(UpdateTaskStates.waiting_for_new_value)


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

        result = await TaskService.update_task_field(task_id, field_to_update, new_value)

        if result["success"]:
            updated_task = await TaskService.get_task_by_id(task_id)
            kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
            deadline_with_tz = updated_task.deadline.replace(tzinfo=kemerovo_tz)

            await message.answer(
                f"Задача успешно обновлена!\n\n"
                f"Название: {updated_task.title}\n"
                f"Описание: {updated_task.description}\n"
                f"Сотрудник: {updated_task.executor.full_name} - {updated_task.executor.position}\n"
                f"Дедлайн: {deadline_with_tz}\n"
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
        kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        deadline_with_tz = selected_task.deadline.replace(tzinfo=kemerovo_tz)

        task_info = (
            f"Задача для изменения:\n\n"
            f"Название: {selected_task.title}\n"
            f"Описание: {selected_task.description}\n"
            f"Сотрудник: {selected_task.executor.full_name} - {selected_task.executor.position}\n"
            f"Дедлайн: {deadline_with_tz.strftime('%d.%m.%Y - %H:%M')}\n"
        )

        await message.answer(task_info)
        await message.answer(
            "Что вы хотите изменить?\n"
            "1 - Название\n"
            "2 - Описание\n"
            "3 - Сотрудник\n"
            "4 - Дедлайн\n"
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

    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    deadline_with_tz = selected_task.deadline.replace(tzinfo=kemerovo_tz)
    await callback_query.message.answer(
        f"Название: {selected_task.title}\n"
        f"Описание: {selected_task.description}\n"
        f"Сотрудник: {selected_task.executor.full_name} - {selected_task.executor.position}\n"
        f"Дедланй: {deadline_with_tz}\n"
    )
    await callback_query.message.answer(
        "Подведите удаление задачи"
        "\nОтправите:"
        "\nда - если уверены"
        "\nнет - если хотите отменить удаление"
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
            "Ошибка ввода"
            "\nОтправите:"
            "\nда - если уверены"
            "\nнет - если хотите отменить удаление"
        )
    await state.clear()


@change_task_router.message(Command("change_task"))
async def get_change_task_keyboard(message: Message):
    keyboard = get_update_task_action_keyboard()
    await message.answer("Изменение существующей задачи", reply_markup=keyboard)