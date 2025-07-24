from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from app.services.user_service import UserService


manager_router = Router()

@manager_router.message(Command("all_workers"))
async def show_all_workers(message: Message):
    users = await UserService.get_all_users()
    workers_list = []
    for i, user in enumerate(users, 1):
        workers_list.append(
            f"{i}. {user.full_name}\n"
            f"   Должность: {user.position or 'не указана'}\n"
        )

    response = "Список всех работников:\n\n" + "\n\n".join(workers_list)
    await message.answer(response)
