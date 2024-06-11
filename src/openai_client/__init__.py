import logging 
import openai
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from config import config
from db_client import session_manager
from sqlalchemy import select, update
from models.models import Assistants, Assistants_Tools, Tools
from openai.types import FunctionDefinition


async def init_client():
    global assistant 
    global db_assistant_id
    global client

    assistant_name = config.assistant_name
    client = AsyncOpenAI()
    
    async with session_manager.session() as s:
        async with s.begin():
            assistant = await init_assistant(assistant_name, s)
            await sync_assistant_with_db(assistant_name, s)
        

async def init_assistant(name : str, session: AsyncSession):
    """
    Entry with name must be specified in the database
    Checks if exist in OpenAI else create an assistant with such name and prompt in the database
    Initializes db_assistant_id
    
    Returns:
        Assistant: assistant
    """
    
    query = select(Assistants).where(Assistants.name == name)
    result = await session.execute(query)
    db_assistant = result.scalars().first()
    
    if not db_assistant:
        raise Exception(f"Assistant: No assistant with name: {config.assistant_name} in database")
    
    global db_assistant_id
    db_assistant_id = db_assistant.id   
    
    if not db_assistant.prompt:
        logging.warning("Assitant: No prompt in the database")
    
    if db_assistant.aid:
        try: 
            logging.debug("Retrieving an assistant by id from db")
            a = openai.beta.assistants.retrieve(db_assistant.aid)
            return a 
        except Exception as e: 
            logging.error(f"Error retrieving assistant by db assistant id")
            logging.error(e)
    else: 
        from .utils import get_assistant
        logging.debug("Retrieving an assistant by name")
        a = await get_assistant(name)
        
    if not a:
        from .utils import create_assistant
        a = await create_assistant(db_assistant.name, db_assistant.prompt)
        logging.warning("Assistant: New OpenAI one created")
    
    db_assistant.aid = a.id
    session.add(db_assistant)
        
    return a
        

async def sync_assistant_with_db(name: str, session: AsyncSession):
    """
    Sets tools, instructions for assistant specified in db
    """
    if not assistant:
        raise ValueError(f"Assistant with name '{name}' was not initialized.")

    # instructions 
    q = select(Assistants.prompt).where(Assistants.id == db_assistant_id)
    result = await session.execute(q)
    prompt = result.scalar()
    
    if prompt:
        openai.beta.assistants.update(assistant.id, instructions=prompt)
        logging.debug("Assistant prompt synchronized with database")

    # tools
    q = select(Tools.src).join(
        Assistants_Tools,
        Assistants_Tools.tool_id == Tools.id
    ).where(
        Assistants_Tools.assistant_id == db_assistant_id
    )
    result = await session.execute(q)
    tools = result.all()
    
    if tools:
        funcs = [{"type" : "function",
                  "function" : FunctionDefinition(**(tool[0]))} 
                 for tool in tools]
        
        openai.beta.assistants.update(assistant.id, tools=funcs)
        logging.debug("Assistant tools synchronized with database")

        q = (
                update(Tools).
                where(Tools.sync == False).
                values(sync=True)
            )

        await session.execute(q)
    else:
        logging.warning("No tools specified")
            
