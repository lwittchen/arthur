import os
import sys 
package_directory = f"{os.getcwd()}//src" 
sys.path.append(package_directory)

import numpy as np
import data_center 

ask_arr = np.array(
    [(21+x, 1, 999+x) for x in range(10)],
    dtype=[("price", float), ("volume", float), ("timestamp", int)],
)
bid_arr = np.array(
    [(19-x, 1, 999-x) for x in range(10)],
    dtype=[("price", float), ("volume", float), ("timestamp", int)],
)

def test_best_bidask():
    orderbook = data_center.OrderBook(bids=bid_arr, asks=ask_arr)
    assert orderbook.best_bid == 19
    assert orderbook.best_ask == 21 

def test_obwa():
    orderbook = data_center.OrderBook(bids=bid_arr, asks=ask_arr)
    obwa_best_bid = orderbook.obwa(side='bid', depth=1)
    obwa_full_bid = orderbook.obwa(side='bid', depth=100)
    obwa_mean_bid = orderbook.obwa(side='bid', depth=50)

    assert obwa_best_bid == 19
    assert obwa_mean_bid == 17
    assert obwa_full_bid == 14.5



