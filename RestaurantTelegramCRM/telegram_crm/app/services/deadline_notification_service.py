from datetime import datetime
from zoneinfo import ZoneInfo
from typing import TYPE_CHECKING

from core.db_helper import db_helper
from core.models import Task
from core.models.base_model import SectorStatus, TaskStatus
from app.repository.task_repository import TaskRepository
from app.services.user_service import UserService

if TYPE_CHECKING:
    from aiogram import Bot

import logging

logger = logging.getLogger(__name__)

class DeadlineNotificationService:
    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")

    async def check_and_notify(self):
        try:
            current_time = datetime.now(self.kemerovo_tz)
            logger.info(f"Проверка уведомлений о дедлайне: {current_time}")

            async with db_helper.session_factory() as session:
                task_repository = TaskRepository(session)
                tasks = await task_repository.get_active_tasks_for_notification()

                tasks_to_update = []

                for task in tasks:
                    try:
                        notification_sent = await self._process_task_notification(task, current_time)
                        if notification_sent:
                            tasks_to_update.append(task)
                    except Exception as e:
                        logger.error(f"Ошибка обработки задачи {task.task_id} для уведомления: {e}")

                if tasks_to_update:
                    for task in tasks_to_update:
                        session.add(task)
                    await session.commit()
                    logger.info(f"Обновлены флаги уведомлений для {len(tasks_to_update)} задач(и).")

        except Exception as e:
            logger.error(f"Критическая ошибка в check_and_notify: {e}")

    async def _process_task_notification(self, task: Task, current_time: datetime) -> bool:
        if task.status != TaskStatus.ACTIVE:
            logger.debug(f"Пропущена задача {task.task_id} со статусом {task.status} для уведомления о дедлайне.")
            return False

        if task.deadline is None:
            logger.debug(f"Пропущена задача {task.task_id} без дедлайна.")
            return False

        if task.deadline.tzinfo is None:
            deadline_aware = task.deadline.replace(tzinfo=self.kemerovo_tz)
        else:
            deadline_aware = task.deadline.astimezone(self.kemerovo_tz)

        time_left = deadline_aware - current_time
        hours_left = time_left.total_seconds() / 3600

        logger.debug(f"Задача {task.task_id}: hours_left = {hours_left:.2f}, "
                    f"24h notified: {task.notified_24_hours}, "
                    f"10h notified: {task.notified_10_hours}, "
                    f"2h notified: {task.notified_2_hours}")

        notification_sent = False

        if 23.0 <= hours_left <= 25.0 and not task.notified_24_hours:
            await self._send_notification(task, "за 24 часа")
            task.notified_24_hours = True
            notification_sent = True
            logger.info(f"Отправлено уведомление 'за 24 часа' по задаче {task.task_id}")

        elif 9.0 <= hours_left <= 11.0 and not task.notified_10_hours:
            await self._send_notification(task, "за 10 часов")
            task.notified_10_hours = True
            notification_sent = True
            logger.info(f"Отправлено уведомление 'за 10 часов' по задаче {task.task_id}")

        elif 1.0 <= hours_left <= 3.0 and not task.notified_2_hours:
            await self._send_notification(task, "за 2 часа")
            task.notified_2_hours = True
            notification_sent = True
            logger.info(f"Отправлено уведомление 'за 2 часа' по задаче {task.task_id}")

        return notification_sent

    async def _send_notification(self, task: Task, timeframe: str):
        if task.deadline.tzinfo is None:
            deadline_str = task.deadline.replace(tzinfo=self.kemerovo_tz).strftime('%d.%m.%Y %H:%M')
        else:
            deadline_str = task.deadline.astimezone(self.kemerovo_tz).strftime('%d.%m.%Y %H:%M')

        message = (
            f"⏰ Уведомление о дедлайне!\n"
            f"Задача: {task.title}\n"
            f"Дедлайн: {timeframe} ({deadline_str})\n"
            f"Описание: {task.description[:100]}{'...' if len(task.description) > 100 else ''}"
        )

        if task.executor_id:
            await self._send_to_user(task.executor_id, message)
        elif task.sector_task:
            await self._send_to_sector(task.sector_task, message)

    async def _send_to_user(self, user_id: int, message: str):
        try:
            await self.bot.send_message(user_id, message)
            logger.info(f"Уведомление отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user_id}: {e}")

    async def _send_to_sector(self, sector: SectorStatus, message: str):
        try:
            users = await UserService.get_users_by_sector(sector)
            sector_names = {
                SectorStatus.BAR: "бару",
                SectorStatus.HALL: "залу",
                SectorStatus.KITCHEN: "кухни"
            }
            sector_name = sector_names.get(sector, "сектору")

            for user in users:
                try:
                    await self.bot.send_message(user.telegram_id, message)
                    logger.info(f"Уведомление отправлено пользователю сектора {sector_name} ({user.telegram_id})")
                except Exception as e:
                    logger.error(f"Ошибка отправки пользователю сектора {sector_name} ({user.telegram_id}): {e}")
        except Exception as e:
            logger.error(f"Ошибка получения пользователей сектора {sector} или отправки уведомлений: {e}")