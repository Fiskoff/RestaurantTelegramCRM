import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from core.config import settings


bot = Bot(settings.tg.token)
dispatcher = Dispatcher()


@dispatcher.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Hello, {message.from_user.first_name}!")


async def main():
    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")

