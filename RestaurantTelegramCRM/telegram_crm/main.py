import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import settings
from app.handlers import all_routers
from app.middlewares.overdue_checker_middleware import OverdueCheckerMiddleware
from app.middlewares.access_middleware import CommandAccessMiddleware

from app.services.notification_service import init_notifier

logging.basicConfig(level=logging.INFO)
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('app.services.notification_service').setLevel(logging.WARNING)
logging.getLogger('app.middlewares.overdue_checker_middleware').setLevel(logging.WARNING)
logging.getLogger('app.services.deadline_notification_service').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def main():
    bot = Bot(
        token=settings.tg.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    init_notifier(bot)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    overdue_middleware = OverdueCheckerMiddleware(bot, check_interval=60)
    dp.message.middleware(overdue_middleware)
    dp.callback_query.middleware(overdue_middleware)

    dp.message.middleware(CommandAccessMiddleware())

    dp.include_routers(all_routers)

    try:
        await dp.start_polling(bot)
    finally:
        if hasattr(overdue_middleware, 'stop'):
            overdue_middleware.stop()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass