import logging
import openai
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Users_Values, Values, Proofs, Users_Values_Proofs
from sqlalchemy.dialects.postgresql import insert


async def save_value(validated_values: list[dict], user_id: str, session: AsyncSession):
    """
    Save validated values to the database for a given user.
    """
    async with session.begin():
        for value in validated_values:
            logging.debug(f"Here we have a value: {value}")
            value_name = value['value']
            proofs = value['proofs']

            value_result = await session.execute(select(Values).where(Values.name == value_name))
            value_row = value_result.scalar()

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
                user_value_row = user_value_result.scalar()

            for proof_content in proofs:
                logging.debug(f"Here we have a proof: {proof_content}")
                if user_value_row.proof_count < 3:
                    proof_row = Proofs(content=proof_content)
                    session.add(proof_row)
                    await session.flush()

                    user_value_proof_row = Users_Values_Proofs(user_value_id=user_value_row.id, proof_id=proof_row.id)
                    session.add(user_value_proof_row)

                    user_value_row.proof_count += 1


async def validate_value(values: list[dict]) -> list[dict]:
    """
    Validate values using OpenAI API.

    Args:
        values (list[dict]): List of values to validate.

    Returns:
        list[dict]: List of validated values.
    """
    
    prompt = """
    You are given a JSON file 'values' in the following format: [{'value': <value>, 'proofs': [<proof1>, <proof2>, ...]}]. 
    The 'values' contain the names of a person's life values, and the 'proofs' array contains statements made by the person that should justify that the value is important to them. 
    Validate the data as follows:
    For each entry in the 'values' array:
    1) If the 'value' cannot be considered a life value, delete the entry.
    Examples of valid human values: 'family', 'fishing', 'gaming', 'pet', 'collecting stamps'.
    Examples of invalid human values: 'the', 'inside', 'Thomas'
    2) If the 'value' can be considered as a life value, examine each 'proof' in 'proofs':
    'Proof' is a statement that shows the importance of the 'value' from the speaker's perspective. If so, keep it. If not, remove it.
    If after iterating over 'proofs' the 'proofs' array is empty, delete the entry.
    Examples of valid values after validation:
    {'value': 'family', 'proofs': ['I love spending time with my family', 'Family gatherings are important to me']} -> {'value': 'family', 'proofs': ['I love spending time with my family', 'Family gatherings are important to me']}
    {'value': 'the', 'proofs': ['The quick brown fox']} -> None
    {'value': 'pet', 'proofs': ['I have a dog', 'Cats are nice', 'Is that an elephant on PHP logo?']} -> {'value': 'pet', 'proofs': ['I have a dog']}
    {'value': 'gaming', 'proofs': ['Gaming industry is booming right now', 'He played a lot']} -> None
    Return an updated JSON. 
    """
    
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=200,
        temperature=0.75
    )

    validated_values = response.choices[0].text.strip()

    try:
        validated_values = json.loads(validated_values)
    except json.JSONDecodeError:
        logging.error("Failed decoding JSON while validating values")
        return []

    return validated_values