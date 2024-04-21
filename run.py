import asyncio
import logging

from os import getenv
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from app.database.models import async_main
from app.handlers import router
from app.admin import admin


async def main():
    await async_main()
    load_dotenv()
    bot = Bot(token=getenv('TOKEN'))
    dp = Dispatcher()
    dp.include_routers(admin, router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")