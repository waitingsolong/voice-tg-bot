import logging
import aiofiles
from typing import Optional
from config import TEMP_DIR
from .session import authenticate, make_run 
from . import client


async def convert_speech_to_text(mp3_file_path : str, uid : str) -> str:
    with open(mp3_file_path, "rb") as audio_file:
        translation = await client.audio.translations.create(
            model="whisper-1",
            file=audio_file,
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
