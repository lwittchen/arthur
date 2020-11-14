"""
Contains shadow trading engine
--> class to keep track of order, trades and pnl
"""

import numpy as np


class Order:
    """
    Defining possible order types and necessary order information
    """

    def __init__(self, order_id, side, trade_price, volume):
        self.order_id = order_id
        self.side = side
        self.trade_price = trade_price
        self.volume = np.abs(volume)

    def get_cashflow(self):
        """
        Cashflow generated by this order
        """
        factor = 1 if self.side == "sell" else -1
        return self.trade_price * self.volume * factor

    def __format__(self, format_spec):
        return f"{self.side} {self.volume}@{self.trade_price}".__format__(format_spec)


class Backtest:
    """
    Order execution, routing and handling
    """

    def __init__(self):
        self.current_position = 0
        self.cashflows = []
        self.turnover = []
        self.all_orders = []
        self.open_orders = {}
        self.market_state = {}

    def rebalance_position(self, desired_position: int):
        """
        Execute an order to change position from 
        current position to desired position
        """
        volume_to_trade = desired_position - self.current_position
        if volume_to_trade != 0:
            self._execute_order(volume_to_trade)
            self.current_position = desired_position
        pass

    def _execute_order(self, volume: int):
        """
        Execute aggressive Buy/Sell order. Assumes that we get can click
        best bid/ask
        """
        if volume > 0:
            side = "buy"
            trade_price = self.market_state["order_book"].best_ask
        elif volume < 0:
            side = "sell"
            trade_price = self.market_state["order_book"].best_bid
        else:
            assert volume != 0, "Wrong Order Volume - volume==0"

        # create order object
        order_id = self.market_state["time"]
        order = Order(order_id, side, trade_price, volume)
        cashflow = order.get_cashflow()

        # update state
        self.cashflows.insert(0, cashflow)
        self.turnover.insert(0, np.abs(volume))
        self.all_orders.insert(0, order)
        pass

    def update_market_state(self, market_state: dict) -> None:
        """
        Current market context. Contains order book information
        as well as recent trades
        """
        self.market_state = market_state
        return None

    def get_current_profit(self) -> float:
        """
        Current pnl
        """
        return np.sum(self.cashflows) + self.current_position_value()

    def current_position_value(self) -> float:
        """
        Valuation of current open position based on current NBBO
        """
        if self.current_position > 0:
            return self.current_position * self.market_state["order_book"].best_bid
        elif self.current_position < 0:
            return self.current_position * self.market_state["order_book"].best_ask
        else:
            return 0

    def get_last_order(self):
        """
        Get last own order which was send to the market
        """
        return self.all_orders[0] if self.all_orders else "-"
