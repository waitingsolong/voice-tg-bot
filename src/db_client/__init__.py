import asyncio
from config import config
from .session import DatabaseSessionManager


async def init_client():
    global session_manager 
    
    session_manager = DatabaseSessionManager(config.database_url.get_secret_value())


asyncio.run(init_client())