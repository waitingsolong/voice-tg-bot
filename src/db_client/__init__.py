import logging

from config import config
from .session import DatabaseSessionManager


def init_client():
    logging.debug("Initializing database")
    
    global session_manager 
    
    session_manager = DatabaseSessionManager(config.database_url.get_secret_value())
