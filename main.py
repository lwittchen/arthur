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

# user input
depth = 10  # in percentage

# system constants
SLEEP_SECONDS = 2  # in seconds


def main(assets):
    """
    Load and log price information from kraken
    """

    # get krakens server time
    server_time_rfc, _ = kraken.get_server_time()

    # get open high low close data
    ohlc: np.array = kraken.get_ohlc_for_pair(*assets, interval=1)

    # get last trades
    lasttrades: np.array = kraken.get_lasttrades_for_pair(*assets)

    # order book: dict with ask and bid information
    _, asks, bids = kraken.get_orderbook_for_pair(*assets)

    # do some calculations
    best_bid, best_ask, midprice = ut.calc_midprice(bids, asks)
    lastprice, lastprice_time = ut.get_lastprice(lasttrades)

    vw_bid, vw_ask = ut.calc_vw_bid_and_offer(bids, asks, depth)
    imb_bid, imb_ask = ut.calc_imbalances(vw_bid, vw_ask, lastprice) 

    # log output to console
    logging.info("==========")
    logging.info(
        f"Server time: {server_time_rfc}"
    )
    logging.info(f"{'Last Price:':<12}{lastprice:<6.2f}$ at {lastprice_time}")
    logging.info(f"{'Midprice:':<12}{midprice:<6.2f}$")
    logging.info(f"{'Best-Bid:':<10}{best_bid:<6.2f} - {'Best-Ask:':<10}{best_ask:<6.2f}")
    logging.info(f"{'VW-Bid:':<10}{vw_bid:<6.2f} - {'VW-Ask:':<10}{vw_ask:<6.2f}")
    logging.info(f"{'Imb-Bid:':<10}{imb_bid:<6.2f} - {'Imb-Ask:':<10}{imb_ask:<6.2f}")

    # conform to krakens call rate limit
    time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    while True:
        main(assets=("ETH", "USD"))
