import asyncio
import logging 
from openai import AsyncOpenAI
from config import config
from db_client import session_manager
from sqlalchemy.future import select
from models import models

async def init_client():
    global openai_aid
    global client

    client = AsyncOpenAI()
    openai_aid = await init_assistant_get_aid(config.assistant_name)
    

async def init_assistant_get_aid(name : str) -> str:
    """
    Entry with name must be specified in the database
    Checks if exist in OpenAI else create an assistant with such name and prompt in the database
    
    Returns:
        str: OpenAI assistant id
    """
    async with session_manager.session() as session:
        query = select(models.Assistants).where(models.Assistants.name == config.assistant_name)
        result = await session.execute(query)
        db_assistant = result.scalars().first()
        
        if not db_assistant:
            raise Exception(f"Assistant: No assistant with name: {config.assistant_name} in database")
        
        if not db_assistant.prompt:
            logging.error("Assitant: No prompt in the database")
        
        if db_assistant.aid:
            return db_assistant.aid 
         
        from .utils import get_assistant_id
        openai_aid = await get_assistant_id(name)
         
        if not openai_aid:
            from .utils import create_assistant
            openai_assistant = await create_assistant(db_assistant.name, db_assistant.prompt)
            openai_aid = openai_assistant.id
        
        db_assistant.aid = openai_aid
        session.add(db_assistant)
        await session.commit()
            
        return openai_aid

asyncio.run(init_client())