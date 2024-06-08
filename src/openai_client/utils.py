import json
import logging
 
from config import TEMP_DIR, config 
from typing import Optional
from . import client


async def save_messages_to_temp(thread_id: int) -> None:
    messages = await client.beta.threads.messages.list(thread_id=thread_id)
    
    messages_dict = messages.to_dict() if hasattr(messages, 'to_dict') else messages
    temp_file_path = TEMP_DIR / f"messages_{thread_id}.json"

    with open(temp_file_path, 'w') as f:
        json.dump(messages_dict, f, indent=4)

    logging.info(f"Messages for thread {thread_id} saved to {temp_file_path}")


async def get_assistant_id(name : str) -> Optional[str]:
    async for a in client.beta.assistants.list():
        if a.name == name:
            return a.id
    return None


async def create_assistant(name : str, prompt : str, model : str = "gpt-3.5-turbo-1106"):
    return await client.beta.assistants.create(
        name=name,
        instructions=prompt,
        model=model,
    )
