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
def get_server_time()  -> tuple:
    """
    Get current time from Kraken server
    """
    r = requests.get(f"{URL_PUBLIC}/Time")
    if r.status_code == 200:
        server_time_rfc, server_time_unix = r.json()["result"]["rfc1123"], r.json()["result"]["unixtime"]
        logger.debug("Returning server time")
        return server_time_rfc, server_time_unix
    else:
        logging.debug(f"Server Time Request Failed: {r.status_code}")
        return None


def get_orderbook(asset_x: str, asset_z: str) -> tuple:
    """
    Load current order book for asset pair
    """
    r = requests.get(f"{URL_PUBLIC}/Depth?pair={asset_x}{asset_z}")
    if r.status_code == 200:
        orderbook = r.json()["result"][f"X{asset_x}Z{asset_z}"]
        asks, bids = parse_orderbook_into_arr(orderbook)
        logger.debug("Returning order book data")
        return orderbook, asks, bids
    else:
        logger.debug(f"Order Book Request Failed: {r.status_code}")
        return None


def get_ohlc(asset_x: str, asset_z: str, interval: int=1) -> np.array:
    """
    Get OpenHighLowClose data from kraken for specific pair
    Always returns the latest 720 periods
    Interval: period size in minutes
    """
    r = requests.get(f"{URL_PUBLIC}/OHLC?pair={asset_x}{asset_z}&interval={interval}")
    if r.status_code == 200:
        ohlc = r.json()["result"][f"X{asset_x}Z{asset_z}"]
        logger.debug("Returning OHLC data")
        return parse_ohlc_into_arr(ohlc)
    else:
        logger.debug(f"Order Book Request Failed: {r.status_code}")
        return None


def get_lasttrades(asset_x: str, asset_z: str) -> np.array:
    """
    Get last trades from kraken for specific pair
    """
    r = requests.get(f"{URL_PUBLIC}/Trades?pair={asset_x}{asset_z}")
    if r.status_code == 200:
        lasttrades = r.json()["result"][f"X{asset_x}Z{asset_z}"]
        logger.debug("Returning lasttrade data")
        return parse_lasttrades_into_arr(lasttrades)
    else:
        logger.debug(f"Order Book Request Failed: {r.status_code}")
        return None


def parse_orderbook_into_arr(orderbook: list) -> tuple:
    """
    Parse orderbook data from kraken API into np.array for bid and 
    ask side and make sure that the orders are sorted
    """
    ask_arr = np.array(
        [tuple(x) for x in orderbook["asks"]], 
    dtype=[("price", float),
            ("volume", float),
            ("timestamp", int)])
    bid_arr = np.array(
        [tuple(x) for x in orderbook["bids"]], 
    dtype=[("price", float),
            ("volume", float),
            ("timestamp", int)])

    ask_arr = ask_arr[ask_arr['price'].argsort()]
    bid_arr = bid_arr[bid_arr['price'].argsort()[::-1]]

    return ask_arr, bid_arr


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
            ("time", float),
            ("direction", object),
            ("type", object),
            ("misc", object)
        ],
    )
    return lasttrades_arr
