import logging

from typing import Optional
from sqlalchemy import select
from . import client, assistant 
from db_client import session_manager
from models.models import Users
from .utils import (launch_run, get_last_message, handle_requires_action)
    

async def authenticate(uid: str) -> str:
    """
    Returns thread id corresponding to user from the db. 
    Creates such mapping if needed.
    """
    async with session_manager.session() as session:
        q = select(Users.tid).where(Users.uid == uid)
        result = await session.execute(q)
        row = result.first()
        
        if not row:
            logging.debug(f"User {uid} not found in the database")
            thread = await client.beta.threads.create()
            user = Users(uid=uid, tid=thread.id)
            session.add(user)
            await session.commit()
            logging.info(f"User {uid} added to the database")
            return thread.id    

        tid = row[0]
        
        if tid is None:
            thread = await client.beta.threads.create()
            logging.info(f"Thread {thread.id} created for existing user {uid}")
            tid = thread.id
            session.add(user)
            await session.commit()
            return thread.id

        return tid


async def make_run(tid: int, user_id: str, timeout: float = 300.0) -> Optional[str]:
    """
    Runs an assistant for a given thread ID and returns the response in text format
    Handles tool call if needed

    Args:
        timeout (float): Timeout for the assistant run in seconds.

    Returns:
        str: The response in text format.

    Raises:
        Exception: If waiting too long or unexpected status.
    """
    run = await client.beta.threads.runs.create(thread_id=tid, assistant_id=assistant.id, tool_choice='auto')
    status = await launch_run(run, timeout)
    
    if status == "completed":
        return await get_last_message(tid)
    
    if status == 'requires_action':
        logging.debug("Look! It requires an action")
        await handle_requires_action(run, user_id)

        # TODO check if requires_action rewrites messages history
        # so in wouldn't work 
        run = await client.beta.threads.runs.create(thread_id=tid, assistant_id=assistant.id, tool_choice='none')
        status = await launch_run(run, timeout)

        if status == "completed":
            return await get_last_message(tid)

    return None
