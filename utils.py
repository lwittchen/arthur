"""
Generic calculations 
"""
import logging
import numpy as np

#### setup
logger = logging.getLogger(__name__)

#### functions
def calc_vw_price(arr: np.array, limit: int):
    """
    Calculate volume weighted average price for one side 
    of the book
    arr: bid or ask array to calculate the volume weighted
        price on. column order: price-volume-timestamp
    limit: book depth for VWMP calculation
    """
    arr_sorted = arr[arr[:, 0].argsort()]
    idx = np.cumsum(arr_sorted[:, 1]) < limit
    if not idx.any():
        # Make sure that at least the best price
        # is used for the calculation
        idx[0] = True
    avg_price = arr_sorted[idx, 0].mean()
    return avg_price


def calc_vw_midprice(bid_arr: np.array, ask_arr: np.array, volume: int):
    """
    Calculate volume weighted midprice
    bid_arr: bid orders (prices-volume-timestamp)
    ask_arr: ask orders (prices-volume-timestamp)
    volume: volume until which prices should be considered
    """
    ask_vwp = calc_vw_price(ask_arr, volume)
    bid_vwp = calc_vw_price(bid_arr, volume)
    vwmp = np.mean([ask_vwp, bid_vwp])
    logger.debug(f"Returning VWMP: {vwmp}")
    return vwmp


def calc_midprice(bid_arr: np.array, ask_arr: np.array):
    """
    Calculate midprice based on give ask and bid quotes
    Midprice: average between best bid and best ask
    """
    best_ask = ask_arr[:, 0].min()
    best_bid = bid_arr[:, 0].min()
    return np.mean([best_ask, best_bid])
