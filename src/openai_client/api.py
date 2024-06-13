import logging
import aiofiles
import base64
import requests
import logging

from typing import Optional
from config import TEMP_DIR
from .session import authenticate, make_run 
from . import client
from config import config


async def convert_speech_to_text(mp3_file_path : str, uid : str) -> str:
    async with aiofiles.open(mp3_file_path, "rb") as audio_file:
        audio_content = await audio_file.read()
        translation = await client.audio.translations.create(
            model="whisper-1",
            file=audio_content,
            response_format="text"
        )
    
    logging.info(f"User {uid} said: {translation}")
    return translation


async def get_openai_response(prompt: str, uid : str) -> str:
    logging.debug(f"Authenticating user {uid}")
    tid = await authenticate(uid)
    
    await client.beta.threads.messages.create(
        thread_id=tid,
        content=prompt, 
        role='user'
    )
    
    logging.debug("Making a run")
    response = await make_run(tid, uid)
    
    return response


async def convert_text_to_speech(text: str, uid : str) -> Optional[str]:
    mp3_file_path = TEMP_DIR / f"ans_{uid}.mp3"
    
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


async def mood_by_photo(photo_path : str, uid : str) -> Optional[str]:
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