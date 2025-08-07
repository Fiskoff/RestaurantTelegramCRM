from aiogram import Bot
from core.models import Task
from core.models.base_model import SectorStatus
from app.services.user_service import UserService


bot: Bot | None = None


def init_notifier(bot_instance: Bot):
    global bot
    bot = bot_instance


async def _send_message(chat_id: int, message: str):
    if bot is None:
        print("Notifier not initialized!")
        return
    try:
        await bot.send_message(chat_id, message)
    except Exception as e:
        print(f"Failed to send notification: {e}")


async def notify_new_task(task: Task):
    if task.executor_id:
        message = (
            f"Вам назначена новая задача:\n"
            f"Название: {task.title}\n"
            f"Описание: {task.description}\n"
            f"Дедлайн: {task.deadline.strftime('%d.%m.%Y - %H:%M')}\n"
        )
        await _send_message(task.executor_id, message)
    elif task.sector_task:
        users = await UserService.get_users_by_sector(task.sector_task)
        sector_names = {
            SectorStatus.BAR: "бару",
            SectorStatus.HALL: "залу",
            SectorStatus.KITCHEN: "кухни"
        }
        sector_name = sector_names.get(task.sector_task, "сектора")
        message = (
            f"Всему {sector_name} назначена новая задача:\n"
            f"Название: {task.title}\n"
            f"Описание: {task.description}\n"
            f"Дедлайн: {task.deadline.strftime('%d.%m.%Y - %H:%M')}\n"
        )
        for user in users:
            await _send_message(user.telegram_id, message)


async def notify_updated_task(old_task: Task, new_task: Task):
    if old_task.executor_id != new_task.executor_id or old_task.sector_task != new_task.sector_task:
        if old_task.executor_id:
            message = f"Задача \"{old_task.title}\" была переназначена."
            await _send_message(old_task.executor_id, message)
        elif old_task.sector_task:
            users = await UserService.get_users_by_sector(old_task.sector_task)
            message = f"Задача \"{old_task.title}\" была переназначена с вашего сектора."
            for user in users:
                await _send_message(user.telegram_id, message)

    if new_task.executor_id:
        message = (
            f"Вам назначена задача (изменена):\n"
            f"Название: {new_task.title}\n"
            f"Описание: {new_task.description}\n"
            f"Дедлайн: {new_task.deadline.strftime('%d.%m.%Y - %H:%M')}\n"
        )
        await _send_message(new_task.executor_id, message)
    elif new_task.sector_task:
        users = await UserService.get_users_by_sector(new_task.sector_task)
        sector_names = {
            SectorStatus.BAR: "бару",
            SectorStatus.HALL: "залу",
            SectorStatus.KITCHEN: "кухни"
        }
        sector_name = sector_names.get(new_task.sector_task, "сектора")
        message = (
            f"Всему {sector_name} назначена задача (изменена):\n"
            f"Название: {new_task.title}\n"
            f"Описание: {new_task.description}\n"
            f"Дедлайн: {new_task.deadline.strftime('%d.%m.%Y - %H:%M')}\n"
        )
        for user in users:
            await _send_message(user.telegram_id, message)
    else:
        if new_task.executor_id:
            message = (
                f"Изменена задача \"{new_task.title}\":\n"
                f"Новое описание: {new_task.description}\n"
                f"Новый дедлайн: {new_task.deadline.strftime('%d.%m.%Y - %H:%M')}\n"
            )
            await _send_message(new_task.executor_id, message)
        elif new_task.sector_task:
            users = await UserService.get_users_by_sector(new_task.sector_task)
            message = (
                f"Изменена задача для всего сектора \"{new_task.title}\":\n"
                f"Новое описание: {new_task.description}\n"
                f"Новый дедлайн: {new_task.deadline.strftime('%d.%m.%Y - %H:%M')}\n"
            )
            for user in users:
                await _send_message(user.telegram_id, message)


async def notify_deleted_task(task: Task):
    if task.executor_id:
        message = f"Задача \"{task.title}\" была удалена."
        await _send_message(task.executor_id, message)
    elif task.sector_task:
        users = await UserService.get_users_by_sector(task.sector_task)
        message = f"Задача \"{task.title}\", назначенная вашему сектору, была удалена."
        for user in users:
            await _send_message(user.telegram_id, message)
