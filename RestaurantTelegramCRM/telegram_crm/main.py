import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import settings
from app.handlers import all_routers
from app.middlewares.overdue_checker_middleware import OverdueCheckerMiddleware


async def main():
    bot = Bot(settings.tg.token)
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)

    overdue_middleware = OverdueCheckerMiddleware(check_interval=300)
    dispatcher.overdue_middleware = overdue_middleware
    dispatcher.message.middleware(overdue_middleware)
    dispatcher.callback_query.middleware(overdue_middleware)

    dispatcher.include_router(all_routers)

    try:
        await dispatcher.start_polling(bot)
    except KeyboardInterrupt:
        print("Exiting...")
        if hasattr(dispatcher, 'overdue_middleware'):
            dispatcher.overdue_middleware.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
