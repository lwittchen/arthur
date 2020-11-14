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

    def __init__(self, position_size, sleep_seconds):
        self.position_size = position_size
        self.sleep_seconds = sleep_seconds
        self.market_state = dict()
        self._signals = dict()
        self._indicators = dict()
        self.trade_signal = 0
        

    def update_market_state(self, current_state):
        """
        Update state of the market
        """
        self.market_state = current_state
        self.update_indicators()
        self.update_signals()

    @property
    def signals(self) -> dict:
        """
        Returning current/slow/fast rolling signals
        """
        return self._signals

    @property
    def indicators(self) -> dict:
        """
        Return current state of market
        """
        return self._indicators
    
    def update_indicators(self):
        raise NotImplementedError

    def update_signals(self):
        raise NotImplementedError

    @property 
    def desired_position(self) -> int:
        """
        Get desired position suggested by
        the strategy. Make sure that update_market_state
        was called shortly before this function!
        """
        return self.trade_signal * self.position_size


class SobiStrategy(Strategy):
    """
    Storing the current and historic Sobi signals
    """

    def __init__(
        self, window_size: int, theta: float, depth: int, **kwargs
    ):
        super().__init__(**kwargs)
        self._signals = dict(current=0, rolling=0,)
        self.last_signals = []
        self.last_imbalances = []
        self._indicators = dict(
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
        last_price = self.market_state.get("public_trades").last_price
        vw_bid = self.market_state['order_book'].obwa(side='bid', depth=self._depth)
        vw_ask = self.market_state['order_book'].obwa(side='ask', depth=self._depth)

        imb_bid, imb_ask = self._calc_imbalances(
            vw_bid=vw_bid, vw_ask=vw_ask, lastprice=last_price
        )

        # update rolling imbalances
        self.last_imbalances.insert(0, (imb_bid, imb_ask))
        if len(self.last_imbalances) > self._window_size:
            self.last_imbalances.pop()
        rolling_imb_bid, rolling_imb_ask = self._calc_rolling_imbalances()
        
        logger.info(
            f"Updated rolling imbalances: {len(self.last_imbalances)} rolling obs"
        )

        # update indicator dictionary
        self._indicators.update(
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
        imb_bid = self._indicators.get("imb_bid")
        imb_ask = self._indicators.get("imb_ask")
        rolling_imb_bid = self._indicators.get("rolling_imb_bid")
        rolling_imb_ask = self._indicators.get("rolling_imb_ask")

        current_signal = self._calc_signal(
            imb_bid=imb_bid, imb_ask=imb_ask
        )

        if len(self.last_imbalances) == self._window_size:
            # calculate rolling signals
            rolling_signal = self._calc_signal(
                imb_bid=rolling_imb_bid, imb_ask=rolling_imb_ask
            )
            logger.info(
                f"Rolling imbalances: bid={rolling_imb_bid:.4f} and ask={rolling_imb_ask:.4f}"
            )

            # update state
            self._signals.update(
                current=current_signal, rolling=rolling_signal,
            )
            self.trade_signal = self._signals['rolling']
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

    def _calc_signal(self, imb_bid: float, imb_ask: float) -> int:
        """
        Calculate trade signal following the SOBI strategy proposed 
        e.g. in: https://www.cis.upenn.edu/~mkearns/projects/sobi.html
        """
        if (imb_ask - imb_bid) > self._theta:
            # buy signal
            return 1
        elif (imb_bid - imb_ask) > self._theta:
            # sell signal
            return -1
        else:
            # do nothing
            return 0


class TrendStrategy(Strategy):
    def __init__(self, window_size, adx_threshold, **kwargs):
        super().__init__(**kwargs)
        self.window_size = window_size
        self._indicators = dict(adx_idx=None, adx_neg=None, adx_pos=None)
        self._signals = dict(current=None)
        self._adx_threshold = adx_threshold

    def update_indicators(self):
        """
        Get adx indicator
        https://school.stockcharts.com/doku.php?id=technical_indicators:average_directional_index_adx
        """
        ohlc_arr = self.market_state.get("public_trades").ohlc
        ohlc = pd.DataFrame(ohlc_arr)
        adx = ta.trend.ADXIndicator(
            high=ohlc["high"], low=ohlc["low"], close=ohlc["close"], n=self.window_size
        )
        self._indicators.update(
            adx_idx=adx.adx().iat[-1],
            adx_neg=adx.adx_neg().iat[-1],
            adx_pos=adx.adx_pos().iat[-1],
        )
        pass

    def update_signals(self):
        adx_idx = self._indicators.get("adx_idx")
        adx_neg = self._indicators.get("adx_neg")
        adx_pos = self._indicators.get("adx_pos")

        signal = self._calc_signal(adx_idx, adx_neg, adx_pos)

        self._signals.update(current=signal)
        self.trade_signal = self._signals.get('current')
        pass

    def _calc_signal(self, adx_idx, adx_neg, adx_pos) -> int:
        """
        Calculate signal based on trade recommendations on
        https://school.stockcharts.com/doku.php?id=technical_indicators:average_directional_index_adx
        """
        if adx_idx > self._adx_threshold:
            if adx_pos > adx_neg:
                return 1
            elif adx_neg > adx_pos:
                return -1
        else:
            return 0


class WilliamsrStrategy(Strategy):
    def __init__(self, window_size, wr_threshold):
        self.window_size = window_size
        self.indicators = dict(wr_idx=None)
        self.signals = dict(current=None)
        self._wr_threshold = wr_threshold

    def update_indicators(self) -> None:
        """
        Get Williams R indicator
        """
        ohlc_arr = self.market_state.get("public_trades").ohlc
        ohlc = pd.DataFrame(ohlc_arr)
        Indicator = ta.momentum.WilliamsRIndicator(
            high=ohlc["high"], low=ohlc["low"], close=ohlc["close"], lbp=self.window_size
        )
        self.indicators.update(
            wr_idx=Indicator.wr().iat[-1],
        )
        return None

    def update_signals(self) -> None:
        wr_idx = self.indicators.get("wr_idx")
        signal = self._calc_signal(wr_idx)
        self.signals.update(current=signal)
        return None

    def _calc_signal(self, wr_idx: float) -> int:
        """
        Calculate signal based on trade recommendations on
        """
        if wr_idx > -20:
            return -1
        elif wr_idx < -80:
            return 1
        else:
            return 0

