import logging
import json

from . import client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Users_Values, Values, Proofs, Users_Values_Proofs, Users


async def save_value(values: str, uid: str, session: AsyncSession):
    """
    Save validated values to the database for a given user.
    """
    async with session.begin():
        for value in json.loads(values):
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
                    select(Users_Values.id, Users_Values.proof_count).where(
                        Users_Values.user_id == user_id,
                        Users_Values.value_id == value_row.id
                    )
                )
                user_value_row = user_value_result.first()[0]

            for proof_content in proofs:
                logging.debug(f"Here we have a proof: {proof_content}")
                logging.debug(f"USER_VALUE_ROW: {user_value_row} of type {type(user_value_row)}")
                if user_value_row.proof_count < 3:
                    proof_row = Proofs(content=proof_content)
                    session.add(proof_row)
                    await session.flush()

                    user_value_proof_row = Users_Values_Proofs(user_value_id=user_value_row.id, proof_id=proof_row.id)
                    session.add(user_value_proof_row)

                    user_value_row.proof_count += 1
                else:
                    break


# TODO make validate only value's value -> bool
async def validate_value(json_values: str, model='gpt-3.5-turbo-1106') -> str:
    """
    Validate values using tool call.

    Returns:
        str: An updated JSON string
    """
    
    tools = [
        {
              "type": "function",
              "function": {
                "name": "validate_value",
                "description": "Validate the 'values' by following rule: For each object in the 'values' array: 1) If the 'value' cannot be considered a life value, the object is not valid. Valid human values: 'family', 'fishing', 'gaming', 'pet', 'collecting stamps'. Invalid human values: 'the', 'inside', 'Thomas' 2) If the 'value' can be considered as a life value, examine each 'proof' in 'proofs': 'Proof' is a statement that shows the importance of the 'value' from the speaker's perspective. If so, it's valid. If not, remove it. If after iterating over 'proofs' the 'proofs' array is empty, delete the entry. Examples of valid values after validation: {'value': 'family', 'proofs': ['I love spending time with my family', 'Family gatherings are important to me']} -> {'value': 'family', 'proofs': ['I love spending time with my family', 'Family gatherings are important to me']}. {'value': 'the', 'proofs': ['The quick brown fox']} -> None. {'value': 'gaming', 'proofs': ['Gaming industry is booming right now', 'He played a lot']} -> None.",
                "parameters": {
                  "type": "object",
                  "properties": {
                    "values": {
                      "type": "string",
                      "description": "JSON string in the following format: [{'value': <value>, 'proofs': [<proof1>, <proof2>, ...]}]. The 'values' contain the names of a person's life values, and the 'proofs' array contains statements made by the person that should justify that the value is important to them."
                    }
                  },
                  "required": ["values"]
                }
              }
        }
    ]
    
    messages = [{"role": "user", "content": f"{json.dumps(json_values)}"}]
    response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "validate_value"}}
        )
        
    response_message = response.choices[0].message 
    logging.debug(f"Validation response(must be a tool call): {response_message}")

    tool_calls = response_message.tool_calls 
    if not tool_calls: 
        logging.error("No tools came for validation")
        return ""
    
    # TODO try catch 
    tool_values = eval(tool_calls[0].function.arguments)['values']
    
    # Note that messages with role 'tool' must be a response to a preceding message with 'tool_calls'
    messages.append(response_message)
    
    messages.append({
        "role": "tool",
        "tool_call_id":tool_calls[0].id,
        "name": tool_calls[0].function.name,
        "content": "true or false whatever"
    })
    
    model_response_with_function_call = await client.chat.completions.create(
            model=model,
            messages=messages,
    )
    logging.debug(f"The response after tool call: {model_response_with_function_call.choices[0].message.content}")
        
    return tool_values
    