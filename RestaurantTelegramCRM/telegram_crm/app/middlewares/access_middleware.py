from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from app.services.user_service import UserService
from core.models.base_model import UserRole


ROLE_STAFF = "STAFF"
ROLE_MANAGER = "MANAGER"

ACCESS_RULES = {
    ROLE_STAFF: ["my_tasks"],
}

ALL_PROTECTED_COMMANDS = [
    "create_task", "my_tasks", "all_overdue_task",
    "completed_tasks", "change_task", "delete_task", "staff_tasks",
]


class CommandAccessMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        if not isinstance(event, Message):
            return await handler(event, data)

        if not event.text or not event.text.startswith('/'):
            return await handler(event, data)

        command = event.text[1:].split()[0]

        if command == "start":
            return await handler(event, data)

        user_telegram_id = event.from_user.id

        try:
            user = await UserService.get_user_by_telegram_id(user_telegram_id)
            data['user'] = user
        except Exception as e:
            print(f"Ошибка при загрузке пользователя {user_telegram_id}: {e}")
            await event.answer("❌ Ошибка проверки прав доступа. Попробуйте позже.")
            return

        if not user:
            await event.answer(
                "❌ Вы не зарегистрированы в системе. "
                "Обратитесь к администратору."
            )
            return

        user_role = getattr(user, 'role', None)
        has_access = False
        if user_role == UserRole.MANAGER:
            has_access = True
        elif user_role == UserRole.STAFF:
            allowed_commands_for_staff = ACCESS_RULES.get(ROLE_STAFF, [])
            if command in allowed_commands_for_staff:
                has_access = True

        if has_access:
            print(
                f"Пользователь {user.full_name} (ID: {user.telegram_id}, роль: {user_role}) выполнил команду /{command}")
            return await handler(event, data)
        else:
            print(
                f"Пользователю {user.full_name} (ID: {user.telegram_id}, роль: {user_role}) отказано в доступе к команде /{command}")
            await event.answer(
                f"❌ У вас нет прав для выполнения команды /{command}."
            )
            return
