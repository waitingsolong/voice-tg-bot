import logging
import json

from sqlalchemy import select, update
from . import client, assistant 
from db_client import session_manager
from models.models import Users
from .values import save_values, validate_value    


# TODO tid is not used from database, it might be removed
async def authenticate(uid: str) -> str:
    """
    Returns thread id corresponding to user from the db. 
    Creates such mapping if needed.
    
    Returns:
        str: tid
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
        
        if not tid:
            thread = await client.beta.threads.create()
            logging.info(f"Thread {thread.id} created for existing user {uid}")
            tid = thread.id
            q = (
                update(Users).
                where(Users.uid == uid).
                values(tid=tid)
            )
            await session.execute(q)
            await session.commit()
            return thread.id

        return tid


async def make_run(tid: int, uid: str, tool_choice: dict = None, instructions = None):
    """
    Runs an assistant for a given thread ID and returns the response in text format
    Handles tool call if needed
     
    Returns:
        Run: run
    """
    run = await client.beta.threads.runs.create_and_poll(
        thread_id=tid, 
        assistant_id=assistant.id,
        tool_choice=tool_choice,
        timeout = 120.0,
        poll_interval_ms=2000,
        instructions=instructions,
        )
    
    if run.status == "completed":
        return run
    
    elif run.status == 'requires_action':
        logging.debug("Look! It requires an action")
                
        tool_outputs = []

        for tool in run.required_action.submit_tool_outputs.tool_calls:
            logging.debug(f"Tool {tool.function.name}")
    
            if tool.function.name == "save_values":
                values = []
                
                try: 
                    values = eval(tool.function.arguments)['values']
                except Exception as e: 
                    values = []
                    logging.error(f"Error converting values as json")
                    logging.exception(e)
                
                logging.debug(f"Here values before validation: {values}")
                logging.debug("Let's validate values")
                
                validated_values = []
                for value in values:
                    value_name = value['value']
                    is_valid = await validate_value(value_name)
                    if is_valid:
                        validated_values.append(value)

                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": json.dumps(validated_values)
                })

                if validated_values:                    
                    logging.debug("Let's save validated values")
                    try:
                        async with session_manager.session() as session:
                            await save_values(validated_values, uid, session)
                        logging.debug("Validated values saved successfully")
                    except Exception as e:
                        logging.error("Error saving values to database")
                        logging.exception(e)
                else:
                    logging.error("No validated values provided")
                        

        # submit tools
        try:
            run = await client.beta.threads.runs.submit_tool_outputs_and_poll(
              thread_id=tid,
              run_id=run.id,
              tool_outputs=tool_outputs
            )
            logging.debug("Tool outputs submitted successfully.")
        except Exception as e:
            logging.error("Failed to submit tool outputs. Run could be freezed for 10 minuted", e)
            logging.exception(e)

        if run.status != 'completed':
          logging.debug(f"'requires_action' was not properly handled. Run in status: {run.status}")
        
        return run
          
    else:
        logging.error(f"Run failed with status: {run.status}")
        return run
    