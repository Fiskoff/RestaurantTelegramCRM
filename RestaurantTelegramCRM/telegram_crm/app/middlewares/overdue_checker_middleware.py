import asyncio
import logging
from zoneinfo import ZoneInfo
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject

from app.repository.task_repository import TaskRepository
from core.db_helper import db_helper
from app.services.deadline_notification_service import DeadlineNotificationService
from app.services.overdue_notification_service import OverdueNotificationService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OverdueCheckerMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot, check_interval: int = 300): # Note: interval 60 in main.py
        self.bot = bot
        self.check_interval = check_interval
        self.kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        self.check_task = None
        self.is_running = False
        self.notification_service = DeadlineNotificationService(bot)
        self.overdue_notification_service = OverdueNotificationService(bot)


    async def check_overdue_tasks(self) -> int:
        current_time = datetime.now(self.kemerovo_tz)
        updated_count = 0
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            updated_count = await task_repository.update_status_task(current_time)
            if updated_count > 0:
                logger.info(f"Обновлено {updated_count} просроченных задач")

            overdue_tasks_with_users, overdue_tasks_for_sector = await task_repository.get_all_overdue_tasks()

            if not overdue_tasks_with_users and not overdue_tasks_for_sector:
                logger.info("No new overdue tasks found for notification.")
                return updated_count

            logger.info(
                f"Found {len(overdue_tasks_with_users)} new overdue tasks with executor and {len(overdue_tasks_for_sector)} new overdue tasks for sector to notify about.")

            if not hasattr(self, 'overdue_notification_service') or not self.overdue_notification_service:
                logger.warning("OverdueNotificationService not initialized in middleware. Initializing now.")
                self.overdue_notification_service = OverdueNotificationService(self.bot)

            notified_task_ids = []

            for task, user in overdue_tasks_with_users:
                task.executor = user
                try:
                    await self.overdue_notification_service.notify_overdue_task(task)
                    notified_task_ids.append(task.task_id)
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке уведомления о просрочке для задачи {task.task_id} (с исполнителем): {e}")

            for task in overdue_tasks_for_sector:
                try:
                    await self.overdue_notification_service.notify_overdue_task(task)
                    notified_task_ids.append(task.task_id)
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке уведомления о просрочке для задачи {task.task_id} (на сектор): {e}")

            if notified_task_ids:
                try:
                    async with db_helper.session_factory() as update_session:
                        update_repo = TaskRepository(update_session)
                        await update_repo.mark_tasks_as_notified_overdue(notified_task_ids)
                except Exception as e:
                    logger.error(f"Ошибка при обновлении флагов notified_overdue для задач {notified_task_ids}: {e}")
        return updated_count


    async def check_deadline_notifications(self):
        current_time = datetime.now(self.kemerovo_tz)
        logger.info(f"Проверка уведомлений о дедлайне: {current_time}")
        try:
            await self.notification_service.check_and_notify()
        except Exception as e:
            logger.error(f"Ошибка при проверке уведомлений о дедлайне: {e}")


    async def _periodic_check(self):
        self.is_running = True
        logger.info("Сервис проверки задач запущен")
        while self.is_running:
            try:
                await self.check_overdue_tasks()
                await self.check_deadline_notifications()
            except asyncio.CancelledError:
                logger.info("Фоновая задача проверки отменена.")
                break
            except Exception as e:
                logger.error(f"Ошибка в периодической проверке: {e}")
            await asyncio.sleep(self.check_interval)


    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        if self.check_task is None:
            self.check_task = asyncio.create_task(self._periodic_check())
        return await handler(event, data)


    def stop(self):
        self.is_running = False
        if self.check_task:
            self.check_task.cancel()
        logger.info("Сервис проверки просроченных задач остановлен")
