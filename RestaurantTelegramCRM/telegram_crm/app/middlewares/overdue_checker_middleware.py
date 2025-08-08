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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OverdueCheckerMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot, check_interval: int = 300):
        self.bot = bot
        self.check_interval = check_interval
        self.kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        self.check_task = None
        self.is_running = False
        self.notification_service = DeadlineNotificationService(bot)

    async def check_overdue_tasks(self) -> int:
        current_time = datetime.now(self.kemerovo_tz)
        updated_count = 0

        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            # Передаем current_time в метод репозитория
            updated_count = await task_repository.update_status_task(current_time)
            if updated_count > 0:
                logger.info(f"Обновлено {updated_count} просроченных задач")

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
