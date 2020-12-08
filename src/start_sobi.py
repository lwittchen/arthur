"""
Get public price information from Kraken and calculate trade signals based on
Static Order Book Imbalances (sobi)
"""

import time
import logging
import numpy as np

from data_center import DataCenter
import kraken_client
import utils as ut

from strategies import SobiStrategy
from backtest import Backtest

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(filename)s - %(funcName)s: %(message)s",
    datefmt="%m-%d %H:%M:%S",
)


def main(
    pair: str,
    depth: int,
    theta: float,
    window_size: int,
    sleep_seconds: int,
    position_size: float,
):
    """
    Load and log price information from kraken
    """

    sobi_strategy = SobiStrategy(
        window_size=window_size, theta=theta, depth=depth, position_size=position_size
    )
    backtester = Backtest()
    data_center = DataCenter(pair=pair)

    while True:
        # query latest data from exchange
        market_state = data_center.get_market_data()

        # update indicators and signals
        sobi_strategy.update_market_state(current_state=market_state)
        desired_position = sobi_strategy.desired_position

        # create orders and calculate pnl
        backtester.update_market_state(market_state)
        backtester.rebalance_position(desired_position)
        pnl = backtester.get_current_profit()
        last_order = backtester.get_last_order()

        # log output to console
        log_info = dict(
            time_rfc=market_state["time"],
            midprice=market_state["order_book"].midprice,
            best_bid=market_state["order_book"].best_bid,
            best_ask=market_state["order_book"].best_ask,
            **sobi_strategy.indicators,
            **sobi_strategy.signals,
            last_order=last_order,
            pnl=pnl,
        )
        log_msg = ut.get_log_msg(log_info)
        logging.info(log_msg)

        # conform to krakens call rate limit
        time.sleep(sleep_seconds)


if __name__ == "__main__":

    # user inputs
    PAIR = "XETHZUSD"  # payload for kraken server requests
    THETA = 0.5  # threshold variable for the sobi strategy
    DEPTH = 50  # market depth in percentage
    WINDOW_SIZE = 30
    SLEEP_SECONDS = 2  # time between iterations in seconds
    POSITION_SIZE = 0.1

    main(
        pair=PAIR,
        depth=DEPTH,
        theta=THETA,
        window_size=WINDOW_SIZE,
        sleep_seconds=SLEEP_SECONDS,
        position_size=POSITION_SIZE,
    )
