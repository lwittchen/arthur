"""
Interface for the Kraken API
"""
import logging
import requests
import numpy as np
from tenacity import retry, wait_fixed, stop_after_attempt

#### setup
logger = logging.getLogger(__name__)

#### constants
URL_PUBLIC = "https://api.kraken.com/0/public"

#### functions
def get_server_time() -> tuple:
    """
    Get current time from Kraken server
    """
    response = send_public_request(endpoint="Time")
    if response.get("error"):
        logging.info(f"Server Time Request Failed: {response.status_code}")
        return None, None
    else:
        server_time_rfc, server_time_unix = (
            response["result"].get("rfc1123"),
            response["result"].get("unixtime"),
        )
        logger.debug("Returning server time")
        return server_time_rfc, server_time_unix


def get_orderbook(pair: str) -> tuple:
    """
    Load current order book for asset pair
    """
    response = send_public_request(endpoint="Depth", payload={"pair": pair})
    if response.get("error"):
        logging.info(f'Error while loading orderbook data: {response["error"]}')
        return None, None, None
    else:
        orderbook = response["result"].get(pair)
        bids, asks = parse_orderbook_into_arr(orderbook)
        return orderbook, bids, asks


def get_ohlc(pair: str, interval: int = 1) -> np.array:
    """
    Get OpenHighLowClose data from kraken for specific pair
    Always returns the latest 720 periods
    Interval: period size in minutes
    """
    response = send_public_request(
        endpoint="OHLC", payload={"pair": pair, "interval": interval}
    )
    if response.get("error"):
        logging.info(f'Error while loading ohlc data: {response["error"]}')
        return None
    else:
        ohlc_list = response["result"].get(pair)
        ohlc_arr = parse_ohlc_into_arr(ohlc_list)
        return ohlc_arr


def get_lasttrades(pair: str) -> np.array:
    """
    Get last trades from kraken for specific pair
    """
    response = send_public_request(endpoint="Trades", payload={"pair": pair})
    if response.get("error"):
        logging.info(f'Error while loading lasttrades: {response["error"]}')
        return None
    else:
        lasttrades_list = response["result"].get(pair)
        lasttrades_arr = parse_lasttrades_into_arr(lasttrades_list)
        return lasttrades_arr


@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def send_public_request(endpoint: str, payload: dict = None) -> dict:
    """
    Send request to the public kraken endpoint
    kwargs need to be valid query parameters
    """
    # send get request and check for errors
    r = requests.get(f"{URL_PUBLIC}/{endpoint}", params=payload)
    if r.status_code == 200:
        return r.json()
    else:
        logger.warning(f"Request failed with status code: {r.status_code}")
        return {"error": r.status_code}


def parse_orderbook_into_arr(orderbook: list) -> tuple:
    """
    Parse orderbook data from kraken API into np.array for bid and 
    ask side and make sure that the orders are sorted
    """
    ask_arr = np.array(
        [tuple(x) for x in orderbook["asks"]],
        dtype=[("price", float), ("volume", float), ("timestamp", int)],
    )
    bid_arr = np.array(
        [tuple(x) for x in orderbook["bids"]],
        dtype=[("price", float), ("volume", float), ("timestamp", int)],
    )
    bid_arr = bid_arr[bid_arr["price"].argsort()[::-1]]
    ask_arr = ask_arr[ask_arr["price"].argsort()]

    return bid_arr, ask_arr


def parse_ohlc_into_arr(ohlc: list) -> np.array:
    """
    Parse OHLC data from Kraken API into np.array
    From list of lists --> array
    """
    ohlc_arr = np.array(
        [tuple(x) for x in ohlc],
        dtype=[
            ("timestamp", int),
            ("open", float),
            ("high", float),
            ("low", float),
            ("close", float),
            ("vwap", float),
            ("volume", float),
            ("count", int),
        ],
    )
    return ohlc_arr


def parse_lasttrades_into_arr(lasttrades: list) -> np.array:
    """
    Parse last trade data from Kraken API into np.array
    From list of lists --> array
    """
    lasttrades_arr = np.array(
        [tuple(x) for x in lasttrades],
        dtype=[
            ("price", float),
            ("volume", float),
            ("timestamp", int),
            ("direction", object),
            ("type", object),
            ("misc", object),
        ],
    )
    return lasttrades_arr
