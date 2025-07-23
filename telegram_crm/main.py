import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import settings
from app.handlers.registration_handler import register_router


bot = Bot(settings.tg.token)
storage = MemoryStorage()
dispatcher = Dispatcher(storage=storage)
dispatcher.include_router(register_router)

async def main():
    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")

