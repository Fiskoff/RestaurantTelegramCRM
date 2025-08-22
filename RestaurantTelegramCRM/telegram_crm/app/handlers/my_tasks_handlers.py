from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.keyboards.select_all_task_keyboard import format_tasks_list, build_tasks_keyboard
from app.keyboards.task_reply_keyboard import get_task_action_keyboard, get_report_action_keyboard, get_remove_keyboard
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.services.notification_service import notify_manager_task_completed

my_task_router = Router()


class TaskCompletionStates(StatesGroup):
    waiting_for_report = State()
    task_id = State()


def is_task_active(task_deadline: datetime | None, current_time: datetime) -> bool:
    """
    Проверяет, является ли задача активной.
    Задача без дедлайна считается всегда активной.
    """
    if task_deadline is None:
        return True  # Задачи без дедлайна всегда активны
    # Для задач с дедлайном проверяем дату
    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    # Убедимся, что у дедлайна есть таймзона
    if task_deadline.tzinfo is None:
        deadline_with_tz = task_deadline.replace(tzinfo=kemerovo_tz)
    else:
        deadline_with_tz = task_deadline.astimezone(kemerovo_tz)

    return deadline_with_tz > current_time


@my_task_router.message(Command("my_tasks"))
async def get_my_tasks(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id

    user = await UserService.get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return

    user_sector = user.sector

    personal_tasks = await TaskService.get_tasks_user(telegram_id)

    sector_tasks = []
    if user_sector:
        sector_tasks = await TaskService.get_sector_tasks(user_sector)

    all_tasks = list(personal_tasks)
    task_ids = {task.task_id for task in personal_tasks}

    for sector_task in sector_tasks:
        if sector_task.task_id not in task_ids:
            all_tasks.append(sector_task)

    if not all_tasks:
        await message.answer("У вас пока нет личных задач")
        return

    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    current_time = datetime.now(kemerovo_tz)

    active_tasks = [t for t in all_tasks if is_task_active(t.deadline, current_time)]
    overdue_tasks = [t for t in all_tasks if not is_task_active(t.deadline, current_time) and t.deadline is not None]

    active_text = format_tasks_list(active_tasks, "🟢 Активные задачи:")
    overdue_text = format_tasks_list(overdue_tasks, "🔴 Просроченные задачи:")

    full_text = active_text + "\n" + overdue_text if (active_text or overdue_text) else "Нет задач для отображения."

    await message.answer(full_text, parse_mode="HTML")
    keyboard = build_tasks_keyboard(all_tasks)
    await message.answer("Выберите задачу:", reply_markup=keyboard)


@my_task_router.callback_query(lambda c: c.data and c.data.startswith('select_tasks:'))
async def get_task_by_id(callback_query: CallbackQuery, state: FSMContext):
    try:
        task_id_str = callback_query.data.split(':')[1]
        task_id = int(task_id_str)
    except (IndexError, ValueError):
        await callback_query.answer("Ошибка обработки запроса.", show_alert=True)
        return

    task = await TaskService.get_task_by_id(task_id)

    await state.update_data(task_id=task_id)

    if task.deadline is None:
        deadline_str = "Бессрочно"
    else:
        kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        if task.deadline.tzinfo is None:
            deadline_with_tz = task.deadline.replace(tzinfo=kemerovo_tz)
        else:
            deadline_with_tz = task.deadline.astimezone(kemerovo_tz)
        deadline_str = deadline_with_tz.strftime("%d.%m.%Y %H:%M")

    response_text = (
        f"«{task.title}»\n"
        f"📄 Описание задачи: {task.description}\n"
        f"⏰ Дедлайн: {deadline_str}\n"
    )

    reply_keyboard = get_task_action_keyboard()

    await callback_query.message.answer(response_text, reply_markup=reply_keyboard)
    await callback_query.answer()


@my_task_router.message(F.text == "✅ Задача выполнена")
async def task_completed_start(message: Message, state: FSMContext):
    report_keyboard = get_report_action_keyboard()
    await message.answer(
        "Пожалуйста, отправьте отчет о выполнении задачи.\n"
        "Вы можете отправить текстовый комментарий и/или фотографию.\n"
        "После отправки материалов нажмите '📤 Отправить отчёт' или '❌ Отменить отправку отчёта'",
        reply_markup=report_keyboard
    )
    await state.set_state(TaskCompletionStates.waiting_for_report)


@my_task_router.message(F.text == "📤 Отправить отчёт")
async def send_report(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != TaskCompletionStates.waiting_for_report:
        return

    user_data = await state.get_data()
    task_id = user_data.get("task_id")
    comments = user_data.get("comments", [])
    photos = user_data.get("photos", [])

    comment = "\n".join(comments) if comments else None
    photo_url = ",".join(photos) if photos else None

    task = await TaskService.get_task_by_id(task_id)

    executor_id = None
    if not task.executor_id:
        executor_id = message.from_user.id

    result = await TaskService.complete_task(task_id, comment, photo_url, executor_id)

    if result["success"]:
        try:
            updated_task = await TaskService.get_task_by_id(task_id)
            employee_user = await UserService.get_user_by_telegram_id(message.from_user.id)
            employee_name = f"{employee_user.full_name} - {employee_user.position}" if employee_user else "Неизвестный сотрудник"

            await notify_manager_task_completed(updated_task, employee_name)
        except Exception as notify_error:
            print(f"Ошибка при отправке уведомления менеджеру о выполнении задачи {task_id}: {notify_error}")

        await message.answer(
            "✅ Отчёт успешно отправлен!\n"
            "Задача отмечена как выполненная!",
            reply_markup=get_remove_keyboard()
        )

    await state.clear()
    await show_tasks_list(message)


@my_task_router.message(F.text == "❌ Отменить отправку отчёта")
async def cancel_report(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != TaskCompletionStates.waiting_for_report:
        return

    await state.clear()

    await message.answer(
        "↩️ Отправка отчёта отменена.\n"
        "Задача не была выполнена.",
        reply_markup=get_remove_keyboard()
    )

    await show_tasks_list(message)


@my_task_router.message(TaskCompletionStates.waiting_for_report, F.text)
async def handle_comment(message: Message, state: FSMContext):
    current_data = await state.get_data()
    comments = current_data.get("comments", [])
    comments.append(message.text)
    await state.update_data(comments=comments)
    await message.answer("✅ Комментарий сохранен. Можете отправить еще комментарии, фотографии или выбрать действие.")


@my_task_router.message(TaskCompletionStates.waiting_for_report, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id

    current_data = await state.get_data()
    photos = current_data.get("photos", [])
    photos.append(file_id)
    await state.update_data(photos=photos)
    await message.answer("📸 Фотография сохранена. Можете отправить еще материалы или выбрать действие.")


async def show_tasks_list(message: Message):
    telegram_id = message.from_user.id
    tasks = await TaskService.get_tasks_user(telegram_id)

    if not tasks:
        await message.answer("У вас пока нет задач.")
        return

    kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
    current_time = datetime.now(kemerovo_tz)

    active_tasks = [t for t in tasks if is_task_active(t.deadline, current_time)]
    overdue_tasks = [t for t in tasks if not is_task_active(t.deadline, current_time) and t.deadline is not None]

    active_text = format_tasks_list(active_tasks, "🟢 Активные задачи:")
    overdue_text = format_tasks_list(overdue_tasks, "🔴 Просроченные задачи:")

    full_text = active_text + "\n" + overdue_text if (active_text or overdue_text) else "Нет задач для отображения."

    await message.answer(full_text, parse_mode="HTML")

    keyboard = build_tasks_keyboard(tasks)
    await message.answer("Выберите задачу:", reply_markup=keyboard)


@my_task_router.message(lambda message: message.text == "📋 Вернуться к списку задач")
async def return_to_tasks_list(message: Message, state: FSMContext):
    await state.clear()

    await message.answer("↩️ Возвращаемся к списку задач...", reply_markup=get_remove_keyboard())

    await show_tasks_list(message)