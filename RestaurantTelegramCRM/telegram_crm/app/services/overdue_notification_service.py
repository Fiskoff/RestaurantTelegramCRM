import logging
from typing import TYPE_CHECKING

from core.models import Task, SectorStatus
from app.services.user_service import UserService


if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


class OverdueNotificationService:
    def __init__(self, bot: "Bot"):
        self.bot = bot

    async def _send_message(self, chat_id: int, text: str):
        if not self.bot:
            logger.error("Bot instance is not provided to OverdueNotificationService. Cannot send message.")
            return
        try:
            await self.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            logger.info(f"Overdue notification sent successfully to user {chat_id}.")
        except Exception as e:
            logger.error(f"Failed to send overdue notification to user {chat_id}: {e}")


    async def notify_overdue_task(self, task: Task):
        if not self.bot:
            logger.warning("Bot instance not provided to OverdueNotificationService, skipping overdue task notification.")
            return

        try:
            if task.manager_id:
                manager_message = (
                    f"⚠️ <b>Задача просрочена!</b>\n"
                    f"<b>Задача:</b> {task.title}\n"
                    f"<b>Назначена:</b> "
                )
                if task.executor:
                    manager_message += f"{task.executor.full_name or task.executor.full_name or 'N/A'} ({task.executor.position})"
                elif task.sector_task:
                    sector_names = {
                        SectorStatus.BAR: "Бар",
                        SectorStatus.HALL: "Зал",
                        SectorStatus.KITCHEN: "Кухне"
                    }
                    manager_message += f"сектору '{sector_names.get(task.sector_task, task.sector_task.value)}'"
                else:
                    manager_message += "неизвестно"
                manager_message += "\nПожалуйста, примите меры."

                await self._send_message(task.manager_id, manager_message)
                logger.info(f"Overdue notification sent to manager {task.manager_id} for task {task.task_id}")
            else:
                logger.warning(f"Task {task.task_id} has no manager assigned for overdue notification.")

            overdue_message = f"⚠️ <b>Задача просрочена!</b>\n<b>Задача:</b> {task.title}"

            if task.executor_id and task.executor:
                await self._send_message(task.executor_id, overdue_message)
                logger.info(f"Overdue notification sent to executor {task.executor_id} for task {task.task_id}")
            elif task.sector_task:
                try:
                    users_in_sector = await UserService.get_users_by_sector(task.sector_task)
                    if users_in_sector:
                        sector_display_names = {
                            SectorStatus.BAR: "Бар",
                            SectorStatus.HALL: "Зал",
                            SectorStatus.KITCHEN: "Кухня"
                        }
                        sector_name = sector_display_names.get(task.sector_task, str(task.sector_task))
                        sector_message = f"{overdue_message}\n(Для сектора: {sector_name})"

                        for user in users_in_sector:
                            await self._send_message(user.telegram_id, sector_message)
                            logger.info(f"Overdue notification sent to sector user {user.telegram_id} for task {task.task_id}")
                    else:
                        logger.info(f"No users found in sector {task.sector_task} for overdue notification of task {task.task_id}")
                except Exception as e:
                    logger.error(f"Error getting users for sector {task.sector_task} or sending notifications: {e}")
            else:
                 logger.info(f"Task {task.task_id} is overdue but has no executor or sector assigned. No executor notification sent.")

        except Exception as e:
            logger.error(f"Error in notify_overdue_task for task {task.task_id}: {e}")

