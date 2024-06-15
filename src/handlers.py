import logging
import os

from aiogram import Bot, Router, types, F
from aiogram.types import FSInputFile
from aiogram.filters.command import Command
from openai_client.api import convert_speech_to_text, get_openai_response, convert_text_to_speech, mood_by_photo
from config import PICS_DIR, AUDIO_DIR
from amplitude_client import track_event
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from redis.asyncio.client import Redis
from aiogram.fsm.storage.redis import RedisStorage
from openai_client.session import authenticate
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import StateFilter


router = Router()
# redis_client =redis=Redis(host='redis', port=6379, db=0)
# storage = RedisStorage(redis_client)
storage = MemoryStorage()


class Form(StatesGroup):
    tid = State()


@router.message(StateFilter(None))
async def init_handler(message: types.Message, state: FSMContext):
    await state.set_state(Form.tid)
    
    uid = str(message.from_user.id)
    logging.debug(f"Authenticating user {uid}")
    tid = await authenticate(uid)
    logging.debug(f"User {uid} authentificated")
    
    await message.reply("You were authentificated. Please, come again")
    
    await state.update_data(tid=tid)
    

@router.message(Command("start"))
async def handle_start_command(message: types.Message):
    await track_event(message.from_user.id, "Start command")
    
    await message.answer("Let me hear you")


@router.message(F.voice)
async def handle_voice_message(message: types.Message, bot: Bot, state: FSMContext):
    uid = str(message.from_user.id)
    voice = message.voice
    
    logging.debug(f"Handling voice message for user {uid}")
    await track_event(uid, "Voice Message Received")
    
    # speech to text
    logging.debug(f"Speech to text for user {uid}")
    voice_req_path = AUDIO_DIR / f"{voice.file_unique_id}.mp3"
    await bot.download(voice, voice_req_path)
    try: 
        text = await convert_speech_to_text(voice_req_path, uid)
    finally:
        if os.path.exists(voice_req_path):
            os.remove(voice_req_path)
        
    # text to text
    logging.debug(f"Text to text for user {uid}")
    tid = (await state.get_data())['tid']
    response_text = await get_openai_response(text, uid, tid, "spy")
    if not response_text: 
        logging.error("No response given from text to text")
        await message.reply("Ummm.. Ahhhh...")
        return 
    
    logging.info(f"Assistant want say: {response_text}")
    
    # text to speech
    logging.debug(f"Text to speech for user {uid}")
    voice_ans_path = await convert_text_to_speech(response_text, uid)
     
    if voice_ans_path is not None:
        logging.info(f"Sending voice to {uid}")
        await message.reply_voice(voice=FSInputFile(voice_ans_path))
    else:
        logging.error(f"Failed to create voice message for {uid}")
        await message.reply("Sorry, I can't voice. My mom is in the room")
        await message.reply(response_text)
        
        
@router.message(F.photo)
async def handle_photo(message: types.Message, bot: Bot):
    uid = str(message.from_user.id)
    photo = message.photo[-1]
    
    await track_event(uid, "Photo Received")
    
    photo_req_path = PICS_DIR / f"{photo.file_unique_id}.jpg"
    await bot.download(photo, photo_req_path)
    try: 
        resp = await mood_by_photo(photo_req_path, uid)
    finally:
        os.remove(photo_req_path)
    
    if not resp:
        await message.reply("It's look like I'm blind. I can't see")
    else:
        await message.reply(resp)
        

@router.message(F.text)
async def handle_text_message(message: types.Message, state: FSMContext):
    uid = str(message.from_user.id)
    text = message.text
    
    # text to text
    tid = (await state.get_data())['tid']
    response_text = await get_openai_response(text, uid, tid, "doctor")
    if not response_text: 
        logging.error("No response given from text to text")
        await message.reply("Ummm.. Ahhhh...")
        return 
    
    logging.info(f"Assistant want text: {response_text}")
    await message.reply(response_text)
    