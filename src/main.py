import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import config
from logs import init_logs


async def main() -> None:
    init_logs()
    
    from db_client import init_client as init_db_client
    init_db_client()
    
    from openai_client import init_client as init_openai_client
    await init_openai_client()
    
    from amplitude_client import init_client as init_amplitude_client 
    await init_amplitude_client()
    
    from handlers import router, storage
    bot = Bot(token=config.telegram_token.get_secret_value())
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        logging.debug("Storage connection closed")
        await bot.session.close()
        logging.debug("Bot session closed")


if __name__ == "__main__":
    asyncio.run(main())
    