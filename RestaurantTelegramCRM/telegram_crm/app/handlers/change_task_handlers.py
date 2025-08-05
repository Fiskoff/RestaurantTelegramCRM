from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from app.keyboards.delete_task_keyboars import build_delete_tasks_keyboard
from app.keyboards.task_reply_keyboard import get_update_task_action_keyboard
from app.services.task_service import TaskService


change_task_router = Router()


class TaskDeleteUpdateStates(StatesGroup):
    waiting_for_task_id = State()
    waiting_for_confirmation = State()


@change_task_router.message(F.text == "❌ Удалить задачу")
async def delete_task(message: Message):
    tasks = await TaskService.get_all_task()
    task_keyboard = build_delete_tasks_keyboard(tasks)
    await message.answer("Выберите задачу для удаления:", reply_markup=task_keyboard)


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