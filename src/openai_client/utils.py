import json
import logging

from typing import Optional
from . import client   
from config import TEMP_DIR, config


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


def find_bool(s : str) -> Optional[bool]:
    s = s.lower()
    if 'false' in s:
        return False 
    elif 'true' in s:
        return True
    else:
        return None
    
def get_tool_choice(mode: str = None) -> Optional[dict]:
    """
    Args:
        mode (str): "file" | "func" | None 
    """
    if mode is None:
        return None
    elif mode == "doctor":
        return {"type": "file_search"}
    elif mode == "spy":
        return { "type": "function", "function": {"name": "save_values"} }
    else:
        logging.warning("Unspecified mode for request")
        return None 
    

def get_instructions(mode: str = None) -> Optional[str]:
    """
    Args:
        mode (str): "file" | "func" | None 
    """
    if mode is None:
        return None
    elif mode == "doctor":
        return """You have a manual in format question-answer. Answer no more than you were asked. Try to find the answer there, if not: pretend to be dead. If you used file to answer text it name in the end"""
    elif mode == "spy" and config.assistant_name != "Pam":
        return """You are a live interlocutor. You are really involved in the conversation with the user and are ready to help him answer any request, you want to know more about his personality. At the same time, you are an undercover spy. Your task: to reveal the personality of your interlocutor from different sides, to find out his life values. As the conversation progresses, ask leading questions and you can clarify details that interest you. Be interested in different things."""
    else:
        logging.warning("Unspecified mode for request")
        return None 
    
    
async def get_completed_run_else_None(run):
    if run.status == 'completed':
        return run
    