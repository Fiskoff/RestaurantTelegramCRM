import logging
from typing import TYPE_CHECKING

from core.models import Task, SectorStatus
from app.services.user_service import UserService

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)

_bot_instance: 'Bot | None' = None

def init_notifier(bot: 'Bot'):
    global _bot_instance
    _bot_instance = bot
    logger.info("Notifier service initialized with bot instance.")

async def _send_message(chat_id: int, text: str):
    if not _bot_instance:
        logger.error("Bot instance is not initialized. Cannot send message.")
        return

    try:
        await _bot_instance.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        logger.info(f"Notification sent successfully to user {chat_id}.")
    except Exception as e:
        logger.error(f"Failed to send notification to user {chat_id}: {e}")

async def notify_new_task(task: Task):
    if not _bot_instance:
        logger.warning("Bot instance not initialized, skipping new task notification.")
        return

    try:
        if task.deadline is not None:
            deadline_str = task.deadline.strftime('%d.%m.%Y - %H:%M')
        else:
            deadline_str = "Бессрочно"

        if task.executor_id:
            logger.info(f"Sending new task notification to executor {task.executor_id}.")
            message_text = (
                f"🔔 <b>Вам назначена новая задача!</b>\n\n"
                f"<b>Задача:</b> {task.title}\n"
                f"<b>Описание:</b> {task.description}\n"
                f"<b>Дедлайн:</b> {deadline_str}"
            )
            await _send_message(task.executor_id, message_text)

        elif task.sector_task:
            logger.info(f"Sending new task notification to sector {task.sector_task}.")

            users_in_sector = await UserService.get_users_by_sector(task.sector_task)

            sector_display_names = {
                SectorStatus.BAR: "Бар",
                SectorStatus.HALL: "Зал",
                SectorStatus.KITCHEN: "Кухня"
            }
            sector_name = sector_display_names.get(task.sector_task, str(task.sector_task))

            message_text = (
                f"🔔 <b>Новая задача для вашего сектора ({sector_name})!</b>\n\n"
                f"<b>Задача:</b> {task.title}\n"
                f"<b>Описание:</b> {task.description}\n"
                f"<b>Дедлайн:</b> {deadline_str}"
            )

            for user in users_in_sector:
                await _send_message(user.telegram_id, message_text)

        else:
            logger.info("New task created without executor or sector. No notification sent.")

    except Exception as e:
        logger.error(f"Error in notify_new_task for task {task.task_id}: {e}")

async def notify_updated_task(old_task: Task, new_task: Task):
    if not _bot_instance:
        logger.warning("Bot instance not initialized, skipping updated task notification.")
        return

    try:
        if (old_task.executor_id and old_task.executor_id != new_task.executor_id) or \
                (old_task.sector_task and old_task.sector_task != new_task.sector_task):

            if old_task.executor_id:
                logger.info(f"Sending reassignment notification to old executor {old_task.executor_id}.")
                message_text = f"ℹ️ Задача <b>\"{old_task.title}\"</b> была переназначена с вас."
                await _send_message(old_task.executor_id, message_text)

            elif old_task.sector_task:
                logger.info(f"Sending reassignment notification to old sector {old_task.sector_task}.")
                users_in_old_sector = await UserService.get_users_by_sector(old_task.sector_task)
                sector_display_names = {
                    SectorStatus.BAR: "Бар",
                    SectorStatus.HALL: "Зал",
                    SectorStatus.KITCHEN: "Кухня"
                }
                old_sector_name = sector_display_names.get(old_task.sector_task, str(old_task.sector_task))
                message_text = f"ℹ️ Задача <b>\"{old_task.title}\"</b> была переназначена с вашего сектора ({old_sector_name})."

                for user in users_in_old_sector:
                    await _send_message(user.telegram_id, message_text)

        if new_task.executor_id:
            logger.info(f"Sending updated task notification to new executor {new_task.executor_id}.")
            if new_task.deadline is not None:
                deadline_str = new_task.deadline.strftime('%d.%m.%Y - %H:%M')
            else:
                deadline_str = "Бессрочно"
            message_text = (
                f"✏️ <b>Вам назначена задача (изменена)!</b>\n\n"
                f"<b>Задача:</b> {new_task.title}\n"
                f"<b>Новое описание:</b> {new_task.description}\n"
                f"<b>Новый дедлайн:</b> {deadline_str}"
            )
            await _send_message(new_task.executor_id, message_text)

        elif new_task.sector_task:
            logger.info(f"Sending updated task notification to new sector {new_task.sector_task}.")
            users_in_new_sector = await UserService.get_users_by_sector(new_task.sector_task)
            sector_display_names = {
                SectorStatus.BAR: "Бар",
                SectorStatus.HALL: "Зал",
                SectorStatus.KITCHEN: "Кухня"
            }
            new_sector_name = sector_display_names.get(new_task.sector_task, str(new_task.sector_task))
            if new_task.deadline is not None:
                deadline_str = new_task.deadline.strftime('%d.%m.%Y - %H:%M')
            else:
                deadline_str = "Бессрочно"
            message_text = (
                f"✏️ <b>Изменена задача для всего сектора ({new_sector_name})!</b>\n\n"
                f"<b>Задача:</b> {new_task.title}\n"
                f"<b>Новое описание:</b> {new_task.description}\n"
                f"<b>Новый дедлайн:</b> {deadline_str}"
            )

            for user in users_in_new_sector:
                await _send_message(user.telegram_id, message_text)

    except Exception as e:
        logger.error(f"Error in notify_updated_task for task {new_task.task_id}: {e}")

async def notify_deleted_task(task: Task):
    if not _bot_instance:
        logger.warning("Bot instance not initialized, skipping deleted task notification.")
        return

    try:
        if task.executor_id:
            logger.info(f"Sending deleted task notification to executor {task.executor_id}.")
            message_text = f"🗑️ Задача <b>\"{task.title}\"</b> была удалена."
            await _send_message(task.executor_id, message_text)

        elif task.sector_task:
            logger.info(f"Sending deleted task notification to sector {task.sector_task}.")
            users_in_sector = await UserService.get_users_by_sector(task.sector_task)
            sector_display_names = {
                SectorStatus.BAR: "Бар",
                SectorStatus.HALL: "Зал",
                SectorStatus.KITCHEN: "Кухня"
            }
            sector_name = sector_display_names.get(task.sector_task, str(task.sector_task))
            message_text = f"🗑️ Задача <b>\"{task.title}\"</b>, назначенная вашему сектору ({sector_name}), была удалена."

            for user in users_in_sector:
                await _send_message(user.telegram_id, message_text)

        else:
            logger.info("Deleted task had no executor or sector. No notification sent.")

    except Exception as e:
        logger.error(f"Error in notify_deleted_task for task {task.task_id}: {e}")

async def notify_manager_task_completed(task: Task, employee_full_name: str):
    if not _bot_instance:
        logger.warning("Bot instance not initialized, skipping manager task completion notification.")
        return

    if not task.manager_id:
        logger.info(f"Task {task.task_id} has no manager assigned. No manager notification sent.")
        return

    try:
        message_text = (
            f"✅ <b>Отчёт по задаче</b>\n\n"
            f"<b>Задача:</b> {task.title}\n"
            f"<b>Выполнил(а):</b> {employee_full_name}\n"
        )

        if task.comment:
            escaped_comment = task.comment.replace("&", "&amp;").replace("<", "<").replace(">", ">")
            message_text += f"<b>Комментарий:</b> {escaped_comment}\n"
        else:
            message_text += f"<b>Комментарий:</b> Нет комментария\n"

        photo_count = 0
        if task.photo_url:
            photo_urls = [url.strip() for url in task.photo_url.split(',') if url.strip()]
            photo_count = len(photo_urls)

        if photo_count > 0:
            message_text += f"\n📸 <b>Прикреплено {photo_count} фото.</b>"

        logger.info(f"Sending task completion notification to manager {task.manager_id}.")
        await _send_message(task.manager_id, message_text)

    except Exception as e:
        logger.error(f"Error in notify_manager_task_completed for task {task.task_id}: {e}")