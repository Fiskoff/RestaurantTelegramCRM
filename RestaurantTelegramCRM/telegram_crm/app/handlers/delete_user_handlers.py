from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.services.user_service import UserService

delete_user_router = Router()


class UserDeleteUpdateStates(StatesGroup):
    waiting_for_user_id = State()


@delete_user_router.message(Command("delete_user"))
async def start_delete_user(message: Message, state: FSMContext):
    users_in_db = await UserService.get_all_users()
    if not users_in_db:
        await message.answer("В системе нет сотрудников")
        return

    users = []
    for user in users_in_db:
        users.append(
            f"ID: {user.telegram_id} {user.full_name}-{user.position}"
        )
    users_string = "\n".join(users)
    await message.answer(f"Сотрудники:\n{users_string}")
    await message.answer("Введите ID сотрудника, которого хотите удалить")
    await state.set_state(UserDeleteUpdateStates.waiting_for_user_id)


@delete_user_router.message(UserDeleteUpdateStates.waiting_for_user_id)
async def process_delete_user(message: Message, state: FSMContext):
    try:
        id_user_delete = int(message.text)

        if id_user_delete == message.from_user.id:
            await message.answer("Вы не можете удалить самого себя!")
            await start_delete_user(message, state)
            return

        result = await UserService.delete_user(id_user_delete)

        if result["success"]:
            await message.answer(f"✅ {result['message']}")
            await state.clear()
        else:
            await message.answer(f"❌ {result['message']}")
            await start_delete_user(message, state)

    except ValueError:
        await message.answer("Пожалуйста, введите корректный числовой ID")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
        await state.clear()