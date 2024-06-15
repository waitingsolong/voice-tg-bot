from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    telegram_token: SecretStr
    openai_api_key: SecretStr
    amplitude_api_key : SecretStr
    database_url : SecretStr
    assistant_name : str
    filename : str
    
    debug : bool
    echo_sql : bool

    class Config:
        env_file = '.env'

config = Settings()


import os
from pathlib import Path


TEMP_DIR = Path("temp")
AUDIO_DIR = TEMP_DIR / "audio"
PICS_DIR = TEMP_DIR / "pics"
DATA_DIR = Path("data")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(PICS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)