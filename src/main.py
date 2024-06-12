import logging
import asyncio

from aiogram import Bot, Dispatcher
from config import config


def init_logs():
    FORMAT = "%(levelname)s [%(filename)s->%(funcName)s():%(lineno)s] %(message)s"
    LEVEL = logging.DEBUG
    HANDLERS=[logging.StreamHandler()]
    if config.debug:
        HANDLERS.append(logging.FileHandler("log.log", mode='w'))
        
    logging.basicConfig(level=LEVEL,
                        format=FORMAT, 
                        handlers=HANDLERS,
    )
    
    import pydantic, aiogram, openai, sqlalchemy, alembic, asyncio
    
    libraries = [
        "pydantic",
        "aiogram",
        "openai",
        "sqlalchemy",
        "alembic",
        "asyncio"
    ]
    
    for lib in libraries:
        logging.getLogger(lib).setLevel(logging.WARNING)
        
    logging.getLogger("aiogram").setLevel(logging.INFO)
    
    
init_logs()


async def main() -> None:
    from db_client import init_client as init_db_client
    init_db_client()
    
    from openai_client import init_client as init_openai_client
    await init_openai_client()
    
    from handlers import router
    bot = Bot(token=config.telegram_token.get_secret_value())
    dp = Dispatcher()
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    