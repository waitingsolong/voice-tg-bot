import asyncio

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
    
    from handlers import router
    bot = Bot(token=config.telegram_token.get_secret_value())
    dp = Dispatcher()
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    