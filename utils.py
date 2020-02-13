"""
Generic calculations 
"""
import logging
import numpy as np
import pytz
from datetime import datetime

#### setup
logger = logging.getLogger(__name__)

#### functions
def calc_vw_price(arr: np.array, depth: int) -> float:
    """
    Calculate volume weighted average price for one side 
    of the book
    arr: bid or ask array to calculate the volume weighted
        price on. columns: price-volume-timestamp
    depth: percentage of total volume for the respective side 
        which should be used for price calculation
    """
    volume_total = np.sum(arr['volume'])
    volume_share = volume_total * depth / 100

    idx = np.cumsum(arr['volume']) < volume_share
    if not idx.any():
        # Make sure that at least the best price
        # is used for the calculation
        idx[0] = True
    avg_price = arr['price'][idx].mean()
    return avg_price


def calc_vw_bid_and_offer(bids: np.array, asks: np.array, depth: int) -> float:
    """
    Calculate volume weighted midprice
    bid_arr: bid orders (prices-volume-timestamp)
    ask_arr: ask orders (prices-volume-timestamp)
    depth: percentage of total volume for the respective side 
        which should be used for price calculation
    """
    vw_bid = calc_vw_price(bids, depth)
    vw_ask = calc_vw_price(asks, depth)
    return vw_bid, vw_ask


def calc_midprice(bids: np.array, asks: np.array) -> float:
    """
    Calculate midprice based on give ask and bid quotes
    Midprice: average between best bid and best ask
    """
    best_ask = asks['price'].min()
    best_bid = bids['price'].max()
    return best_bid, best_ask, np.mean([best_ask, best_bid])


def get_lastprice(lasttrades: np.array) -> float:
    """
    Last price = max execution time
    """
    idx = np.argmax(lasttrades['time'])
    return lasttrades['price'][idx], parse_unix_ts(lasttrades['time'][idx])


def parse_unix_ts(timestamp: int) -> datetime:
    """
    convert unix timestamp to datetime object and localize it to 
    CET timezone
    """
    tz_utc = pytz.utc
    temp_datetime = datetime.utcfromtimestamp(int(timestamp))
    return tz_utc.localize(temp_datetime)


def calc_imbalances(vw_bid: float, vw_ask: float, lastprice: float):
    """
    Calculate buy and sell imbalances following the SOBI strategy proposed 
    e.g. in: https://www.cis.upenn.edu/~mkearns/projects/sobi.html
    """
    return lastprice-vw_bid, vw_ask-lastprice