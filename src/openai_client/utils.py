import json
import logging

from typing import Optional
from . import client   
from config import TEMP_DIR


async def save_messages_to_temp(thread_id: int) -> None:
    messages = await client.beta.threads.messages.list(thread_id=thread_id)
    
    messages_dict = messages.to_dict() if hasattr(messages, 'to_dict') else messages
    temp_file_path = TEMP_DIR / f"messages_{thread_id}.json"

    with open(temp_file_path, 'w') as f:
        json.dump(messages_dict, f, indent=4)

    logging.info(f"Messages for thread {thread_id} saved to {temp_file_path}")


async def get_assistant(name : str):
    async for a in client.beta.assistants.list():
        if a.name == name:
            return a
    return None


async def create_assistant(name : str, prompt : str, model : str = "gpt-3.5-turbo-1106"):
    return await client.beta.assistants.create(
        name=name,
        instructions=prompt,
        model=model,
    )
    

async def get_last_message(thread_id: str) -> Optional[str]:
    messages = await client.beta.threads.messages.list(thread_id=thread_id)
    return messages.data[0].content[0].text.value if messages.data else None
