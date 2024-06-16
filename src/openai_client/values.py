import logging

from . import client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Users_Values, Values, Proofs, Users_Values_Proofs, Users
from .utils import find_bool


async def save_values(values: list[dict], uid: str, session: AsyncSession):
    """
    Save validated values to the database for a given user.
    """
    async with session.begin():
        for value in values:
            logging.debug(f"Here we have a value: {value}")
            value_name = value['value']
            proofs = value['proofs']

            value_result = await session.execute(select(Values.id).where(Values.name == value_name))
            value_row = value_result.scalar()
            
            user_result = await session.execute(select(Users.id).where(Users.uid == uid))
            user_id = user_result.scalar()
            
            if value_row is None:
                value_row = Values(name=value_name)
                session.add(value_row)
                await session.flush()

                user_value_row = Users_Values(user_id=user_id, value_id=value_row.id)
                session.add(user_value_row)
                await session.flush()
            else:
                user_value_result = await session.execute(
                    select(Users_Values).where(
                        Users_Values.user_id == user_id,
                        Users_Values.value_id == value_row.id
                    )
                )
                user_value_row = user_value_result.scalars().first()

            for proof_content in proofs:
                logging.debug(f"Here we have a proof: {proof_content}")
                if user_value_row.proof_count < 3:
                    proof_row = Proofs(content=proof_content)
                    session.add(proof_row)
                    await session.flush()

                    user_value_proof_row = Users_Values_Proofs(user_value_id=user_value_row.id, proof_id=proof_row.id)
                    session.add(user_value_proof_row)

                    user_value_row.proof_count += 1
                else:
                    break


async def validate_value(value_name: str, model='gpt-3.5-turbo-1106') -> bool:
    """
    Validate a single value using tool call and return True or False.
    """
    tools = [
        {
              "type": "function",
              "function": {
                "name": "foo",
                "description": "Whatever",
                "parameters": {
                  "type": "object",
                  "properties": {
                    "is_valid": {
                      "type": "boolean",
                      "description": "Indicator which shows if 'value' is truly a life value. If 'value' cannot be considered a life value then 'is_valid_life_value' is true, else false. Example of valid human values: 'family', 'fishing', 'gaming', 'pet', 'collecting stamps'. Invalid human values: 'the', 'inside', 'Thomas'."
                    }
                  },
                  "required": ["is_valid"]
                }
              }
        }
    ]
    
    messages = [{"role": "user", "content": f"value={value_name}"}]
    response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "foo"}}
        )
        
    response_message = response.choices[0].message 
    logging.debug(f"Validation response (must be a tool call): {response_message}")

    tool_calls = response_message.tool_calls 
    if not tool_calls: 
        logging.error("No tools came for validation")
        return False
    
    is_valid = False
    try:        
        arg = tool_calls[0].function.arguments
        logging.debug(f"Tool call arguments: {arg}")
        is_valid = find_bool(arg)
        
        if is_valid is None:
            logging.error(f"Value {value_name} validation is failed. {is_valid} returned")
        else:
            logging.debug(f"Value {value_name} validated successfully: {is_valid}")
            
    except Exception as e:
        logging.error(f"Value {value_name} validation is failed. {is_valid} returned")
        logging.exception(e)
    
    # Note that messages with role 'tool' must be a response to a preceding message with 'tool_calls'
    messages.append(response_message)
    
    messages.append({
        "role": "tool",
        "tool_call_id":tool_calls[0].id,
        "name": tool_calls[0].function.name,
        "content": "whatever"
    })
    
    model_response_with_function_call = await client.chat.completions.create(
            model=model,
            messages=messages,
    )
    logging.debug(f"The response after tool call: {model_response_with_function_call.choices[0].message.content}")
        
    return is_valid
    