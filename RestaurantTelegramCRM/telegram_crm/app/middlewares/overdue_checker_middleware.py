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
    def __init__(self, bot: Bot, check_interval: int = 300):
        self.bot = bot
        self.check_interval = check_interval
        self.kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        self.check_task = None
        self.is_running = False
        self.deadline_notification_service = DeadlineNotificationService(bot)
        self.overdue_notification_service = OverdueNotificationService(self.bot)

    async def check_deadline_notifications(self):
        current_time = datetime.now(self.kemerovo_tz)
        logger.info(f"Проверка уведомлений о дедлайне: {current_time}")
        try:
            await self.deadline_notification_service.check_and_notify()
        except Exception as e:
            logger.error(f"Ошибка при проверке уведомлений о дедлайне: {e}")

    async def check_overdue_tasks(self) -> int:
        current_time = datetime.now(self.kemerovo_tz)
        updated_count = 0
        notified_count = 0
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)

            updated_count = await task_repository.update_status_task(current_time)
            if updated_count > 0:
                logger.info(f"Обновлен статус у {updated_count} задач(и) на OVERDUE")

            overdue_tasks_with_users, overdue_tasks_for_sector = await task_repository.get_all_overdue_tasks()

            if not overdue_tasks_with_users and not overdue_tasks_for_sector:
                logger.debug("Нет новых просроченных задач для уведомления.")
                return updated_count

            logger.info(
                f"Найдено {len(overdue_tasks_with_users)} новых просроченных задач с исполнителем и {len(overdue_tasks_for_sector)} новых просроченных задач для сектора.")

            notified_task_ids = []

            for task_tuple in overdue_tasks_with_users:
                task, user = task_tuple
                task.executor = user
                try:
                    await self.overdue_notification_service.notify_overdue_task(task)
                    notified_task_ids.append(task.task_id)
                    notified_count += 1
                    logger.debug(f"Уведомление о просрочке отправлено для задачи с исполнителем {task.task_id}")
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке уведомления о просрочке для задачи {task.task_id} (с исполнителем): {e}")

            for task in overdue_tasks_for_sector:
                try:
                    await self.overdue_notification_service.notify_overdue_task(task)
                    notified_task_ids.append(task.task_id)
                    notified_count += 1
                    logger.debug(f"Уведомление о просрочке отправлено для задачи на сектор {task.task_id}")
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке уведомления о просрочке для задачи {task.task_id} (на сектор): {e}")

            if notified_task_ids:
                try:
                    await task_repository.mark_tasks_as_notified_overdue(notified_task_ids)
                    logger.info(f"Обновлены флаги notified_overdue для {len(notified_task_ids)} задач.")
                except Exception as e:
                    logger.error(f"Ошибка при обновлении флагов notified_overdue для задач {notified_task_ids}: {e}")

            if notified_count > 0:
                logger.info(f"Отправлено уведомлений о просрочке по {notified_count} новым задачам.")

        return updated_count

    async def _periodic_check(self):
        self.is_running = True
        logger.info("Сервис проверки задач запущен")
        while self.is_running:
            try:
                await self.check_deadline_notifications()
                await self.check_overdue_tasks()
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