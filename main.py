"""
Get public price information from Kraken
"""

import time
import logging
import numpy as np

import kraken
import utils as ut

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(filename)s - %(funcName)s: %(message)s",
    datefmt="%m-%d %H:%M:%S",
)

# constants
VOL_LIMIT = 500
SLEEP_SECONDS = 2


def main(assets):
    """
    Load and log price information from kraken
    """

    while True:
        # get krakens server time
        server_time = kraken.get_server_time()

        # order book: dict with ask and bid information
        order_book = kraken.get_order_book_for_pair(*assets)

        # ask and bid array consist of: price-volume-timestamp
        ask_arr = np.array(order_book["asks"]).astype(float)
        bid_arr = np.array(order_book["bids"]).astype(float)

        # do some calculation
        mp = ut.calc_midprice(bid_arr, ask_arr)
        vwmp = ut.calc_vw_midprice(bid_arr, ask_arr, VOL_LIMIT)

        # log output to console
        logging.info("==========")
        logging.info(f"Server time: {server_time}")
        logging.info(f"Midprice: {mp:.2f}$")
        logging.info(f"VWMP: {vwmp:.2f}$")

        # conform to krakens call rate limit
        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    main(assets=("ETH", "USD"))
