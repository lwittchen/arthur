import numpy as np
import utils as ut

class SobiStrategy:
    """
    Storing the current and historic Sobi signals
    """

    def __init__(self, window_size_fast: float, window_size_slow: float, theta: float, depth: float):
        self.signals = dict(
            current=0,
            rolling=0,
        )
        self.indicators= dict(
            fast=0,
            slow=0
        )
        self.last_signals = []
        self.market_state = {}

        self._size_fast = window_size_fast
        self._size_slow = window_size_slow
        self._theta = theta
        self._depth = depth

    def update_signals(self):
        """
        Update current Signal
        """
        imb_bid = self.market_state.get('imb_bid')
        imb_ask = self.market_state.get('imb_ask')
        current_signal = ut.calc_sobi_signals(imb_bid=imb_bid, imb_ask=imb_ask, theta=self._theta)

        # update last signal
        self.last_signals.insert(0, current_signal)
        if len(self.last_signals) > self._size_slow:
            self.last_signals.pop()

            # calculate rolling signals
            fast_indicator = np.mean(self.last_signals[:self._size_fast])
            slow_indicator = np.mean(self.last_signals)
            rolling_signal = 1 if fast_indicator > slow_indicator else -1

            # update state
            self.signals.update(
                current=current_signal,
                rolling=rolling_signal,
            )
            self.indicators.update(
                fast=fast_indicator,
                slow=slow_indicator
            )
        pass

    def update_market_state(self, bids: np.array, asks: np.array, lasttrades: np.array):
        """
        Calculate all necessary parameter to get the sobi signal
        """
        vw_bid, vw_ask = ut.calc_vw_bid_and_offer(bids=bids, asks=asks, depth=self._depth)
        lastprice, _ = ut.get_lastprice(lasttrades=lasttrades)
        imb_bid, imb_ask = ut.calc_imbalances(vw_bid=vw_bid, vw_ask=vw_ask, lastprice=lastprice)
        
        self.market_state.update(
            vw_bid=vw_bid,
            vw_ask=vw_ask,
            lastprice=lastprice,
            imb_bid=imb_bid,
            imb_ask=imb_ask
        )
        pass

    def get_all_signals(self):
        """
        Returning current/slow/fast rolling signals
        """
        return self.signals

    def get_rolling_signal(self):
        """
        Return final signal based on fast and slow moving average
        Long (1) if fast > slow
        Short (-1) if fast < slow
        """
        return self.signals['rolling']

    def get_market_state(self):
        """
        Return current state of market
        """
        return self.market_state