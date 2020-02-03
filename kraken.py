"""
Interface for the Kraken API
"""
import logging
import requests
import numpy as np

#### setup
logger = logging.getLogger(__name__)

#### constants
URL_PUBLIC = "https://api.kraken.com/0/public"

#### functions
def get_server_time():
    """
    Get current time from Kraken server
    """
    r = requests.get(f"{URL_PUBLIC}/Time")
    if r.status_code == 200:
        server_time = r.json()["result"]["rfc1123"]
        logger.debug("Returning server time")
        return server_time
    else:
        logging.debug(f"Server Time Request Failed: {r.status_code}")
        return None


def get_order_book_for_pair(x: str, z: str):
    """
    Load current order book for asset pair
    """
    r = requests.get(f"{URL_PUBLIC}/Depth?pair={x}{z}")
    if r.status_code == 200:
        order_book = r.json()["result"][f"X{x}Z{z}"]
        logger.debug("Returning order book data")
        return order_book
    else:
        logger.debug(f"Order Book Request Failed: {r.status_code}")
        return None
