"""
Get public price information from Kraken and calculate trade signals based on
Static Order Book Imbalances (sobi)
"""

import time
import logging
import numpy as np

import kraken
import utils as ut

from strategies import SobiStrategy

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(filename)s - %(funcName)s: %(message)s",
    datefmt="%m-%d %H:%M:%S",
)


def main(params: dict, depth: int, theta: float, sleep_seconds: int):
    """
    Load and log price information from kraken
    """

    sobi_strategy = SobiStrategy(window_size_fast=10, window_size_slow=60, theta=theta, depth=depth)

    while True:

        # krakens server time
        server_time_rfc, _ = kraken.get_server_time()

        # last 720 open high low close periods
        ohlc: np.array = kraken.get_ohlc(params, interval=1)

        # XXX last trades
        lasttrades: np.array = kraken.get_lasttrades(params)

        # orderbook: dict with ask/bid information - asks and bids are arrays
        _, bids, asks = kraken.get_orderbook(params)

        # check if all data is available -> if not, continue iterations

        # do stuff
        best_bid, best_ask, midprice = ut.calc_midprice(bids, asks)
        sobi_strategy.update_market_state(bids=bids, asks=asks, lasttrades=lasttrades)
        sobi_strategy.update_signals()

        market_state = sobi_strategy.get_market_state()
        signals = sobi_strategy.get_all_signals()

        # results
        current_state = dict(
            time=server_time_rfc,
            midprice=midprice,
            best_bid=best_bid,
            best_ask=best_ask,
            **market_state, 
            **signals
        )

        # log output to console
        log_msg = ut.get_log_msg(current_state)
        logging.info(log_msg)

        # conform to krakens call rate limit
        time.sleep(sleep_seconds)


if __name__ == "__main__":

    # user inputs
    PARAMS = {"pair": "XETHZUSD"}  # payload for kraken server requests
    THETA = 0.5  # threshold variable for the sobi strategy
    DEPTH = 25  # market depth in percentage
    SLEEP_SECONDS = 2  # time between iterations in seconds

    main(params=PARAMS, depth=DEPTH, theta=THETA, sleep_seconds=SLEEP_SECONDS)
