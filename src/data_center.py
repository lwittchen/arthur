"""
Class to distribute and preprocess market data
"""
import numpy as np
import kraken_client
import utils


class DataCenter:
    def __init__(self, pair, load_trades: bool = True, load_orderbook: bool = True):
        self.pair = pair
        self.load_server_time = True
        self.load_trades = load_trades
        self.load_orderbook = load_orderbook
        self.init_empty_market_vars()

    def init_empty_market_vars(self) -> None:
        """
        Initiate empty market information
        """
        self.server_time_rfc = None
        self.order_book = None
        self.public_trades = None

    def update_market_data(self) -> None:
        """
        Load most recent data from Kraken
        """

        if self.load_server_time:
            # krakens server time
            self.server_time_rfc, _ = kraken_client.get_server_time()

        if self.load_orderbook:
            # orderbook: dict with ask/bid information - asks and bids are arrays
            _, bids, asks = kraken_client.get_orderbook(pair=self.pair)
            self.order_book = OrderBook(bids=bids, asks=asks)

        if self.load_trades:
            ohlc = kraken_client.get_ohlc(pair=self.pair, interval=1)
            self.public_trades = PublicTrades(ohlc=ohlc)

        return None

    def get_market_data(self):
        """
        Return most recent data
        """
        self.update_market_data()
        return dict(
            time=self.server_time_rfc,
            order_book=self.order_book,
            public_trades=self.public_trades,
        )


class OrderBook:
    def __init__(self, bids: np.array, asks: np.array):
        self.bids = bids
        self.asks = asks

    @property
    def midprice(self) -> float:
        """
        Midprice = mean(best_bid, best_ask)
        """
        best_bid = self.best_bid
        best_ask = self.best_ask
        return np.mean([best_ask, best_bid])

    @property
    def best_bid(self) -> float:
        """
        Maximum bid on the market
        """
        return self.bids["price"][0]

    @property
    def best_ask(self) -> float:
        """ 
        Lower offer on the market
        """
        return self.asks["price"][0]

    def obwa(self, side: str, depth: float) -> float:
        """
        Calculate volumen weighted average order book price
        for the given depth 
        params:
            side: 'bid' or 'ask'
            depth: order book depth in percent of total volume 
                on that side
        """

        # check valid inputs
        if not side in ("bid", "ask") or depth < 0:
            return None

        arr = self.bids if side == "bid" else self.asks
        total_volume = np.sum(arr["volume"])
        obwa_volume = total_volume * depth / 100
        idx = np.cumsum(arr["volume"]) <= obwa_volume

        # Make sure that at least the best price
        # is used for the calculation
        if not idx.any():
            idx[0] = True

        obwa_price = np.sum(arr["price"][idx] * arr["volume"][idx]) / np.sum(
            arr["volume"][idx]
        )

        return obwa_price


class PublicTrades:
    def __init__(self, ohlc: np.array):
        self._ohlc = ohlc

    @property
    def ohlc(self) -> np.array:
        return self._ohlc

    @property
    def last_price(self) -> float:
        """
        Return closing price from latest bar 
        --> last traded price
        """
        idx = np.argmax(self._ohlc["timestamp"])
        return self._ohlc["close"][idx]
