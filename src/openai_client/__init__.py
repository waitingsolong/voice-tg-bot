import asyncio
import logging 
from openai import AsyncOpenAI
from config import config
from db_client import session_manager, models
from sqlalchemy.future import select

async def init_client():
    global global_aid
    global client

    client = AsyncOpenAI()
    global_aid = await init_assistant_get_aid(config.assistant_name)
    

async def init_assistant_get_aid(name : str) -> str:
    """
    Create/use an assistant with given name if it specified in the database via OpenAI
    
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
            logging.warning("Assitant: No prompt in the database")
        
        if not db_assistant.aid: 
            from .utils import create_assistant
            openai_assistant = await create_assistant(db_assistant.name, db_assistant.prompt)
            aid = openai_assistant.id
            
            db_assistant.aid = aid 
            session.add(db_assistant)
            await session.commit()
            
        return aid 

asyncio.run(init_client())