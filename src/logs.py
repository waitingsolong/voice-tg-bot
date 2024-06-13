import logging

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
    
    