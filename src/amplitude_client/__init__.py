import logging

from amplitude import Amplitude
from concurrent.futures import ThreadPoolExecutor
from config import config


async def init_amplitude_client():
    """
    Initialize the Amplitude client and the ThreadPoolExecutor for asynchronous event tracking.
    """
    logging.debug("Initializing amplitude")
    
    global amplitude_client
    global amplitude_executor

    amplitude_client = Amplitude(config.amplitude_api_key.get_secret_value())
    amplitude_executor = ThreadPoolExecutor(max_workers=5)


async def track_event(user_id : str, event_name : str, event_properties : dict = {}):
    """
    Track an event asynchronously using the Amplitude client.
    
    Args:
        event_name (str): The name of the event.
        user_id (str): The ID of the user.
        event_properties (dict, optional): Additional properties of the event.
    """

    def send_event():
        amplitude_client.track(event={
            'user_id': user_id,
            'event_type': event_name,
            'event_properties': event_properties
        })

    amplitude_executor.submit(send_event)
