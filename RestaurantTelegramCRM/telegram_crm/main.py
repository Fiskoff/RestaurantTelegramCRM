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
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=settings.tg.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    init_notifier(bot)
    logger.info("Notifier service initialized.")

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    overdue_middleware = OverdueCheckerMiddleware(check_interval=60)
    dp.message.middleware(overdue_middleware)
    dp.callback_query.middleware(overdue_middleware)

    dp.message.middleware(CommandAccessMiddleware())

    dp.include_routers(all_routers)

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    finally:
        if hasattr(overdue_middleware, 'stop'):
            overdue_middleware.stop()
            logger.info("Overdue checker middleware stopped.")
        await bot.session.close()
        logger.info("Bot session closed.")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt).")
