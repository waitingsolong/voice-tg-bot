from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    telegram_token: SecretStr
    openai_api_key: SecretStr
    database_url : SecretStr
    
    echo_sql : bool = True
    assistant_name : str

    class Config:
        env_file = '.env'

config = Settings()

import os
from pathlib import Path

TEMP_DIR = Path("temp")
os.makedirs(TEMP_DIR, exist_ok=True)
