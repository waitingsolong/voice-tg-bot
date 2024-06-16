import logging
import aiofiles
import base64
import logging
import uuid

from typing import Optional
from config import AUDIO_DIR
from .session import make_run
from . import client
from .utils import get_tool_choice, get_last_message, get_instructions, get_completed_run_else_None


async def convert_speech_to_text(mp3_file_path : str, uid : str) -> str:
    with open(mp3_file_path, "rb") as audio_file:
        translation = await client.audio.translations.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    
    logging.info(f"User {uid} said: {translation}")
    return translation


async def get_openai_response(prompt: str, uid : str, tid : str, mode = None) -> Optional[None]:
    """
    Modes specify run parameters
    "doctor" - for making answers via file search
    "spy" - for collecting, validating and saving to database life values from user's requests via openai functions api 
     
    Args:
        mode (str): "doctor" | "spy" | None 
    """
    
    await client.beta.threads.messages.create(
        thread_id=tid,
        content=prompt, 
        role='user'
    )
    
    tool_choice = get_tool_choice(mode)
    logging.debug(f"Forced tool choice for request: {tool_choice}")
    
    instructions = get_instructions(mode)
    logging.debug(f"Forced instructions for request: {instructions}")
    
    logging.debug("Making a run")
    run = await make_run(tid, uid, tool_choice=tool_choice, instructions=instructions)
    logging.debug(f"The run itself: {run}")
    
    run = await get_completed_run_else_None(run)
    
    #debug
    messages = await client.beta.threads.messages.list(thread_id=tid)
    logging.debug(f"Messages: {messages}")
    
    if not run:
        return None
    
    return await get_last_message(tid)


async def convert_text_to_speech(text: str, uid : str) -> Optional[str]:
    mp3_file_path = AUDIO_DIR / f"{uid}_{uuid.uuid4().hex}.mp3"
    
    async with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="onyx",
        input=text
    ) as response:
        async with aiofiles.open(mp3_file_path, 'wb') as f:
            async for chunk in response.iter_bytes():
                await f.write(chunk)
    
    if mp3_file_path.exists() and mp3_file_path.stat().st_size > 0:
        return mp3_file_path
    else:
        return None


async def mood_by_photo(photo_path : str) -> Optional[str]:
    def encode_image(image_bytes):
        return base64.b64encode(image_bytes).decode('utf-8')
    
    logging.debug("Detecting a mood by photo")
    
    base64_photo = None 
    async with aiofiles.open(photo_path, 'rb') as file:
        photo_bytes = await file.read()
        base64_photo = encode_image(photo_bytes)
        
    if not base64_photo:
        logging.error("Error processing photo")
        return None

    response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What is the mood of the person in the picture?"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_photo}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300,
        )

    return response.choices[0].message.content