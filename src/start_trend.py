"""
Get public price information from Kraken and calculate trade signals based on
technical indicators
"""

import time
import logging
import numpy as np

import kraken
import utils as ut

from strategies import TrendStrategy
from backtest import Backtest

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(filename)s - %(funcName)s: %(message)s",
    datefmt="%m-%d %H:%M:%S",
)


def main(
    payload: dict,
    window_size: int,
    adx_threshold: int,
    sleep_seconds: int,
    position_size: float,
):
    """
    Load and log price information from kraken
    """

    trend_strategy = TrendStrategy(window_size=window_size, adx_threshold=adx_threshold)
    backtester = Backtest()

    while True:

        # krakens server time
        server_time_rfc, server_time_unix = kraken.get_server_time()

        # last 720 open high low close periods
        ohlc: np.array = kraken.get_ohlc(payload, interval=1)
        _, bids, asks = kraken.get_orderbook(payload)
        best_bid, best_ask, midprice = ut.calc_midprice(bids, asks)

        market_state = dict(
            time=server_time_unix,
            ohlc=ohlc,
            best_bid=best_bid,
            best_ask=best_ask,
            midprice=midprice,
        )

        # check if all data is available -> if not, continue iterations
        # do stuff
        trend_strategy.update_market_state(market_state)
        trend_strategy.update_indicators()
        trend_strategy.update_signals()

        indicators = trend_strategy.get_indicators()
        signals = trend_strategy.get_signals()

        # order routing
        desired_position = signals["current"] * position_size
        backtester.update_market_state(market_state)
        backtester.rebalance_position(desired_position)
        pnl = backtester.get_current_profit()
        last_order = backtester.get_last_order()

        current_state = dict(
            time_rfc=server_time_rfc,
            ohlc=market_state["ohlc"][-1],
            best_bid=best_bid,
            best_ask=best_ask,
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
    PAYLOAD = {"pair": "XETHZUSD"}  # payload for kraken server requests
    WINDOW_SIZE = 30
    ADX_THRESHOLD = 20
    SLEEP_SECONDS = 10  # time between iterations in seconds
    POSITION_SIZE = 0.1

    main(
        payload=PAYLOAD,
        window_size=WINDOW_SIZE,
        adx_threshold=ADX_THRESHOLD,
        sleep_seconds=SLEEP_SECONDS,
        position_size=POSITION_SIZE,
    )
