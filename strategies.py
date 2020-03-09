import numpy as np
import pandas as pd
import utils as ut
import logging
import ta

logger = logging.getLogger(__name__)


class Strategy:
    """
    Generic Strategy function providing getter and setter for 
    signal, indicators and market state
    """

    def __init__(self):
        self.market_state = None
        self.signals = dict()
        self.indicators = dict()

    def update_market_state(self, market_state):
        """
        Update state of the market
        """
        self.market_state = market_state

    def get_signals(self) -> dict:
        """
        Returning current/slow/fast rolling signals
        """
        return self.signals

    def get_indicators(self) -> dict:
        """
        Return current state of market
        """
        return self.indicators


class SobiStrategy(Strategy):
    """
    Storing the current and historic Sobi signals
    """

    def __init__(
        self, window_size: int, theta: float, depth: int,
    ):
        self.signals = dict(current=0, rolling=0,)
        self.last_signals = []
        self.last_imbalances = []
        self.indicators = dict(
            vw_bid=None,
            vw_ask=None,
            imb_bid=None,
            imb_ask=None,
            rolling_imb_bid=None,
            rolling_imb_ask=None,
        )

        self._window_size = window_size
        self._theta = theta
        self._depth = depth

    def update_indicators(self):
        """
        Calculate all necessary indicators to get the sobi signal
        """
        bids = self.market_state.get("bids")
        asks = self.market_state.get("asks")
        lastprice = self.market_state.get("lastprice")

        vw_bid, vw_ask = ut.calc_vw_bid_and_offer(
            bids=bids, asks=asks, depth=self._depth
        )
        imb_bid, imb_ask = self._calc_imbalances(
            vw_bid=vw_bid, vw_ask=vw_ask, lastprice=lastprice
        )

        # update rolling imbalances
        self.last_imbalances.insert(0, (imb_bid, imb_ask))
        if len(self.last_imbalances) > self._window_size:
            self.last_imbalances.pop()
            rolling_imb_bid, rolling_imb_ask = self._calc_rolling_imbalances()
        else:
            rolling_imb_bid = rolling_imb_ask = None
        logger.info(
            f"Updated rolling imbalances: {len(self.last_imbalances)} rolling obs"
        )

        # update indicator dictionary
        self.indicators.update(
            vw_bid=vw_bid,
            vw_ask=vw_ask,
            imb_bid=imb_bid,
            imb_ask=imb_ask,
            rolling_imb_bid=rolling_imb_bid,
            rolling_imb_ask=rolling_imb_ask,
        )
        pass

    def update_signals(self):
        """
        Update current Signal
        """
        imb_bid = self.indicators.get("imb_bid")
        imb_ask = self.indicators.get("imb_ask")
        rolling_imb_bid = self.indicators.get("rolling_imb_bid")
        rolling_imb_ask = self.indicators.get("rolling_imb_ask")

        current_signal = self._calc_signal(
            imb_bid=imb_bid, imb_ask=imb_ask, theta=self._theta
        )

        if len(self.last_imbalances) == self._window_size:
            # calculate rolling signals
            rolling_signal = self._calc_signal(
                imb_bid=rolling_imb_bid, imb_ask=rolling_imb_ask, theta=self._theta
            )
            logger.info(
                f"Rolling imbalances: bid={rolling_imb_bid} and ask={rolling_imb_ask}"
            )

            # update state
            self.signals.update(
                current=current_signal, rolling=rolling_signal,
            )
        pass

    def _calc_rolling_imbalances(self) -> np.array:
        """
        calculate rolling bid and ask imbalances
        """
        return np.mean(self.last_imbalances, axis=0)

    def _calc_imbalances(self, vw_bid: float, vw_ask: float, lastprice: float):
        """
        Calculate buy and sell imbalances following the SOBI strategy proposed 
        e.g. in: https://www.cis.upenn.edu/~mkearns/projects/sobi.html
        """
        bi = lastprice - vw_bid
        si = vw_ask - lastprice
        return bi, si

    def _calc_signal(self, imb_bid: float, imb_ask: float, theta: float) -> int:
        """
        Calculate trade signal following the SOBI strategy proposed 
        e.g. in: https://www.cis.upenn.edu/~mkearns/projects/sobi.html
        """
        if (imb_ask - imb_bid) > theta:
            # buy signal
            return 1
        elif (imb_bid - imb_ask) > theta:
            # sell signal
            return -1
        else:
            # do nothing
            return 0


class TrendStrategy(Strategy):
    def __init__(self, window_size):
        self.window_size = window_size
        self.indicators = dict(adx_idx=None, adx_neg=None, adx_pos=None)
        self.signals = dict(current=None)

    def update_indicators(self):
        """
        Get adx indicator
        https://school.stockcharts.com/doku.php?id=technical_indicators:average_directional_index_adx
        """
        ohlc_arr = self.market_state.get("ohlc")
        ohlc = pd.DataFrame(ohlc_arr)
        adx = ta.trend.ADXIndicator(
            high=ohlc["high"], low=ohlc["low"], close=ohlc["close"], n=self.window_size
        )
        self.indicators.update(
            adx_idx=adx.adx().iat[-1],
            adx_neg=adx.adx_neg().iat[-1],
            adx_pos=adx.adx_pos().iat[-1],
        )
        pass

    def update_signals(self):
        adx_idx = self.indicators.get("adx_idx")
        adx_neg = self.indicators.get("adx_neg")
        adx_pos = self.indicators.get("adx_pos")

        signal = self._calc_signal(adx_idx, adx_neg, adx_pos)

        self.signals.update(current=signal)
        pass

    def _calc_signal(self, adx_idx, adx_neg, adx_pos) -> int:
        """
        Calculate signal based on trade recommendations on
        https://school.stockcharts.com/doku.php?id=technical_indicators:average_directional_index_adx
        """
        if adx_idx > 20:
            if adx_pos > adx_neg:
                return 1
            elif adx_neg > adx_pos:
                return -1
            else:
                return 0
        else:
            return 0
