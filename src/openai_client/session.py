import asyncio
import logging 
from . import client, global_aid   
from db_client import session_manager, models
from sqlalchemy.future import select
    
    
async def check_if_thread_exists(uid: str):
    async with session_manager.session() as session:
        q = select(models.Users).where(models.Users.uid == uid)
        result = await session.execute(q)
        user = result.scalars().first()
        return user.tid if user else None


async def store_thread(uid: str, thread_id: str):
    async with session_manager.session() as session:
        async with session.begin():
            user = models.Users(uid=uid, tid=thread_id)
            session.add(user)
        logging.info(f"Thread {thread_id} created for user {uid}")


async def authenticate(uid: str) -> str:
    tid = await check_if_thread_exists(uid)
    
    if tid is None:
        thread = await client.beta.threads.create()
        store_thread(uid, thread.id)
        tid = thread.id
    
    return tid


async def run_assistant(tid: int) -> str:
    run = await client.beta.threads.runs.create(thread_id=tid, assistant_id=global_aid)

    while run.status != "completed":
        await asyncio.sleep(0.5)
        run = await client.beta.threads.runs.retrieve(thread_id=tid, run_id=run.id)

    messages = await client.beta.threads.messages.list(thread_id=tid)
    
    response = messages.data[0].content[0].text.value
    return response
