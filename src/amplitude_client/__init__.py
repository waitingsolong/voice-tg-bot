import logging

from amplitude import Amplitude, BaseEvent
from concurrent.futures import ThreadPoolExecutor
from config import config


async def init_client():
    """
    Initialize the Amplitude client and the ThreadPoolExecutor for asynchronous event tracking.
    """
    logging.debug("Initializing amplitude")
    
    global amplitude_client
    global amplitude_executor

    amplitude_client = Amplitude(config.amplitude_api_key.get_secret_value())
    amplitude_executor = ThreadPoolExecutor(max_workers=5)


async def track_event(user_id: str, event_name: str, event_properties: dict = {}):
    """
    Track an event asynchronously using the Amplitude client.
    
    Args:
        event_name (str): The name of the event.
        user_id (str): The ID of the user.
        event_properties (dict, optional): Additional properties of the event.
    """

    amplitude_executor.submit(send_event, user_id, event_name, event_properties)


def send_event(user_id: str, event_name: str, event_properties: dict):
    amplitude_client.track(BaseEvent(
        user_id=user_id,
        event_type=event_name,
        event_properties=event_properties
    ))
