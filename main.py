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

# system constants
SLEEP_SECONDS = 2  # in seconds


def main(params, depth, theta):
    """
    Load and log price information from kraken
    """

    # get krakens server time
    server_time_rfc, _ = kraken.get_server_time()

    # get open high low close data
    ohlc: np.array = kraken.get_ohlc(params, interval=1)

    # get last trades
    lasttrades: np.array = kraken.get_lasttrades(params)

    # order book: dict with ask and bid information
    _, asks, bids = kraken.get_orderbook(params)

    # do some calculations
    best_bid, best_ask, midprice = ut.calc_midprice(bids, asks)
    lastprice, lastprice_time = ut.get_lastprice(lasttrades)

    vw_bid, vw_ask = ut.calc_vw_bid_and_offer(bids, asks, depth)
    imb_bid, imb_ask = ut.calc_imbalances(vw_bid, vw_ask, lastprice)
    sobi_signal = ut.calc_sobi_signals(imb_bid, imb_ask, theta)

    # results
    results = dict(
        time=server_time_rfc,
        lastprice=lastprice,
        midprice=midprice,
        best_bid=best_bid,
        best_ask=best_ask,
        vw_bid=vw_bid,
        vw_ask = vw_ask,
        imb_bid=imb_bid,
        imb_ask=imb_ask,
        sobi_signal=sobi_signal
    )

    # log output to console
    log_msg = ut.get_log_msg(results)
    logging.info(log_msg)
    
    # conform to krakens call rate limit
    time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    PARAMS = {"pair": "XETHZUSD"}
    THETA = 0.5
    DEPTH = 10  # in percentage

    while True:
        main(params=PARAMS, depth=DEPTH, theta=THETA)
