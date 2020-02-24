import numpy as np
import utils as ut
import logging

logger = logging.getLogger(__name__)


class SobiStrategy:
    """
    Storing the current and historic Sobi signals
    """

    def __init__(
        self, window_size: int, theta: float, depth: int,
    ):
        self.signals = dict(current=0, rolling=0,)
        self.last_signals = []
        self.last_imbalances = []
        self.indicators = {}

        self._window_size = window_size
        self._theta = theta
        self._depth = depth

    def update_signals(self):
        """
        Update current Signal
        """
        imb_bid = self.indicators.get("imb_bid")
        imb_ask = self.indicators.get("imb_ask")
        current_signal = self.calc_signal(
            imb_bid=imb_bid, imb_ask=imb_ask, theta=self._theta
        )

        if len(self.last_imbalances) == self._window_size:
            # calculate rolling signals
            rolling_imb_bid, rolling_imb_ask = self.calc_rolling_imbalances()
            rolling_signal = self.calc_signal(
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

    def calc_rolling_imbalances(self) -> tuple:
        """
        calculate rolling bid and ask imbalances
        """
        return np.mean(self.last_imbalances, axis=0)

    def update_market_state(self, market_state: dict):
        """
        Calculate all necessary parameter to get the sobi signal
        """
        bids = market_state.get("bids")
        asks = market_state.get("asks")
        lasttrades = market_state.get("lasttrades")

        vw_bid, vw_ask = ut.calc_vw_bid_and_offer(
            bids=bids, asks=asks, depth=self._depth
        )
        lastprice, _ = ut.get_lastprice(lasttrades=lasttrades)
        imb_bid, imb_ask = self.calc_imbalances(
            vw_bid=vw_bid, vw_ask=vw_ask, lastprice=lastprice
        )

        # update rolling imbalances
        self.last_imbalances.insert(0, (imb_bid, imb_ask))
        if len(self.last_imbalances) > self._window_size:
            self.last_imbalances.pop()
        logger.info(
            f"Updated rolling imbalances: {len(self.last_imbalances)} rolling obs"
        )

        # update market state dictionary
        self.indicators.update(
            vw_bid=vw_bid, vw_ask=vw_ask, imb_bid=imb_bid, imb_ask=imb_ask,
        )
        pass

    def calc_imbalances(self, vw_bid: float, vw_ask: float, lastprice: float):
        """
        Calculate buy and sell imbalances following the SOBI strategy proposed 
        e.g. in: https://www.cis.upenn.edu/~mkearns/projects/sobi.html
        """
        bi = lastprice - vw_bid
        si = vw_ask - lastprice
        return bi, si

    def calc_signal(self, imb_bid: float, imb_ask: float, theta: float) -> int:
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

    def get_all_signals(self) -> dict:
        """
        Returning current/slow/fast rolling signals
        """
        return self.signals

    def get_rolling_signal(self) -> int:
        """
        Return final signal based on fast and slow moving average
        Long (1) if fast > slow
        Short (-1) if fast < slow
        """
        return self.signals["rolling"]

    def get_indicators(self) -> dict:
        """
        Return current state of market
        """
        return self.indicators
