"""
Get public price information from Kraken and calculate trade signals based on
Static Order Book Imbalances (sobi)
"""

import time
import logging
import numpy as np

from data_center import DataCenter
from strategies import Strategy
import kraken_client 
import utils as ut

from strategies import SobiStrategy, TrendStrategy
from backtest import Backtest

# todo: change from basicConfig to logger instance
# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(filename)s - %(funcName)s: %(message)s",
    datefmt="%m-%d %H:%M:%S",
)

@ut.timing
def run(
    pair: str,
    strategy: Strategy,
):
    """
    Load and log price information from kraken
    """

    backtester = Backtest()
    data_center = DataCenter(pair=pair)

    while True:
        # query latest data from exchange
        market_state = data_center.get_market_data()

        # update indicators and signals
        strategy.update_market_state(current_state=market_state)
        desired_position = strategy.desired_position

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
            **strategy.indicators,
            current_signal=strategy.trade_signal,
            last_order=last_order,
            pnl=pnl,
        )
        log_msg = ut.get_log_msg(log_info)
        logging.info(log_msg)

        # conform to krakens call rate limit
        time.sleep(strategy.sleep_seconds)


if __name__ == "__main__":

    sobi_strategy = SobiStrategy(
        window_size=10, 
        theta=0.1,  # threshold variable for the sobi strategy 
        depth=30,  # market depth in percentage 
        position_size=0.1,
        sleep_seconds=2
    )

    trend_strategy = TrendStrategy(
        window_size=10,
        adx_threshold=20,
        position_size=0.1,
        sleep_seconds=10
    )

    run(
        pair="XETHZUSD",  # payload for kraken server requests
        strategy=sobi_strategy
    )
