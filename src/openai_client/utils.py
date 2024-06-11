import asyncio
import json
import logging

from typing import Optional
from . import client   
from db_client import session_manager
from config import TEMP_DIR
from .values import save_value, validate_value


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


async def get_last_message(thread_id: int) -> Optional[str]:
    messages = await client.beta.threads.messages.list(thread_id=thread_id)
    return messages.data[0].content[0].text.value if messages.data else None


async def launch_run(run, timeout: float) -> Optional[str]:
    """
    Launch run with timeout until reaching completed status

    Returns:
        Optional[str]: Status in [success_statuses, fail_statuses] else None
    """
    success_statuses = ["completed", "requires_action"]
    fail_statuses = ["failed", "cancelled", "expired"]
    
    async def check_run_status():
        while True:
            if run.status in success_statuses:
                return 
            elif run.status in fail_statuses:
                logging.error(f"Run was {run.status}: {run.id}")
                return
            await asyncio.sleep(1)

    try:
        await asyncio.wait_for(check_run_status(), timeout=timeout)
    except asyncio.TimeoutError:
        logging.error(f"Run {run.id} failed within {timeout} seconds with status {run.status}")
        return None
    
    return run.status


# TODO test
async def handle_requires_action(run, user_id: str):
    for tool in run.required_action.submit_tool_outputs.tool_calls:
        logging.debug(f"Ok it's tool there: {tool.function.name}")
        if tool.function.name == 'save_value':
            values = json.loads(tool.function.arguments)
            logging.debug(f"Here values json: {values}")
            logging.debug("Let's validate values")
            validated_values = await validate_value(values)

            if validated_values:
                logging.debug("Wow, it's some validated values which would be saved now")
                logging.debug(f"Here values json: {validated_values}")
                logging.debug("Let's save validated values")
                async with session_manager.session() as session:
                    await save_value(validated_values, user_id, session)
