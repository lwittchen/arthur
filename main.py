"""
Get public price information from Kraken
"""

import time
import logging

import requests
import numpy as np

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(filename)s %(funcName)s %(message)s",
    datefmt="%m-%d %H:%M:%S",
)

# constants
URL_PUBLIC = "https://api.kraken.com/0/public"
VOL_LIMIT = 500
SLEEP_SECONDS = 2

# get current unix time
def get_server_time():
    """
    Get current time from Kraken server
    """
    r = requests.get(f"{URL_PUBLIC}/Time")
    if r.status_code == 200:
        server_time = r.json()["result"]["rfc1123"]
        return server_time
    else:
        logging.info(f"Server Time Request Failed: {r.status_code}")
        return None


def get_order_book_for_pair(x: str, z: str):
    """
    Load current order book for asset pair
    """
    r = requests.get(f"{URL_PUBLIC}/Depth?pair={x}{z}")
    if r.status_code == 200:
        server_time_unix = r.json()["result"][f"X{x}Z{z}"]
        return server_time_unix
    else:
        logging.info(f"Order Book Request Failed: {r.status_code}")
        return None


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
    ask_vwmp = calc_vw_price(ask_arr, volume)
    bid_vwmp = calc_vw_price(bid_arr, volume)
    vwmp = np.mean([ask_vwmp, bid_vwmp])
    return vwmp


def calc_midprice(bid_arr: np.array, ask_arr: np.array):
    """
    Calculate midprice based on give ask and bid quotes
    Midprice: average between best bid and best ask
    """
    best_ask = ask_arr[:, 0].min()
    best_bid = bid_arr[:, 0].min()
    return np.mean([best_ask, best_bid])


def main(assets):
    """
    Load and log price information from kraken
    """
    # get krakens server time
    server_time = get_server_time()

    # order book: dict with ask and bid information
    order_book = get_order_book_for_pair(*assets)

    # ask and bid array consist of: price-volume-timestamp
    ask_arr = np.array(order_book["asks"]).astype(float)
    bid_arr = np.array(order_book["bids"]).astype(float)

    # do some calculation
    mp = calc_midprice(bid_arr, ask_arr)
    vwmp = calc_vw_midprice(bid_arr, ask_arr, VOL_LIMIT)

    # log outout to console
    logging.info("==========")
    logging.info(f"Server time: {server_time}")
    logging.info(f"Midprice: {mp:.2f}$")
    logging.info(f"VWMP: {vwmp:.2f}$")


if __name__ == "__main__":
    while True:
        main(assets=("ETH", "USD"))

        # conform to krakens call rate limit
        time.sleep(SLEEP_SECONDS)
