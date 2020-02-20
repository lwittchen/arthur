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
from backtest import Backtest

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(filename)s - %(funcName)s: %(message)s",
    datefmt="%m-%d %H:%M:%S",
)


def main(params: dict, depth: int, theta: float, window_size: int, sleep_seconds: int, position_size: float):
    """
    Load and log price information from kraken
    """

    sobi_strategy = SobiStrategy(
        window_size=window_size, theta=theta, depth=depth
    )
    backtester = Backtest()

    while True:

        # krakens server time
        server_time_rfc, server_time_unix = kraken.get_server_time()

        # # last 720 open high low close periods
        # ohlc: np.array = kraken.get_ohlc(params, interval=1)

        # XXX last trades
        lasttrades: np.array = kraken.get_lasttrades(params)

        # orderbook: dict with ask/bid information - asks and bids are arrays
        _, bids, asks = kraken.get_orderbook(params)
        best_bid, best_ask, midprice = ut.calc_midprice(bids, asks)
        market_state = dict(            
            time=server_time_unix,
            bids=bids,
            asks=asks,
            midprice=midprice,
            best_bid=best_bid,
            best_ask=best_ask,
            lasttrades=lasttrades
        )

        # check if all data is available -> if not, continue iterations

        # do stuff
        

        sobi_strategy.update_market_state(market_state)
        sobi_strategy.update_signals()

        indicators = sobi_strategy.get_indicators()
        signals = sobi_strategy.get_all_signals()

        # order routing
        desired_position = signals['rolling'] * position_size
        backtester.update_market_state(market_state)
        backtester.rebalance_position(desired_position)
        pnl = backtester.get_current_profit()
        last_order = backtester.get_last_order()

        # results
        # if pnl != 0:
        #     breakpoint()

        current_state = dict(
            time_rfc=server_time_rfc,
            midprice=market_state['midprice'],
            best_bid=market_state['best_bid'],
            best_ask=market_state['best_ask'],
            **indicators,
            **signals,
            last_order=last_order,
            pnl=pnl,
        )

        # log output to console
        log_msg = ut.get_log_msg(current_state)
        logging.info(log_msg)

        # conform to krakens call rate limit
        time.sleep(sleep_seconds)


if __name__ == "__main__":

    # user inputs
    PARAMS = {"pair": "XETHZUSD"}  # payload for kraken server requests
    THETA = 0  # threshold variable for the sobi strategy
    DEPTH = 25  # market depth in percentage
    WINDOW_SIZE = 10
    SLEEP_SECONDS = 2  # time between iterations in seconds
    POSITION_SIZE = 0.1

    main(params=PARAMS, depth=DEPTH, theta=THETA, window_size=WINDOW_SIZE, sleep_seconds=SLEEP_SECONDS, position_size=POSITION_SIZE)
