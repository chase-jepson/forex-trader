from __future__ import annotations

from datetime import UTC, datetime

from forex_trader.broker.base import Broker
from forex_trader.domain.enums import OrderSide, PositionStatus
from forex_trader.domain.models import PIP_SIZE, OrderResult, Position, Quote, new_id


class SimulatedBroker(Broker):
    """In-memory broker with realistic fill modeling.

    Buys fill at the ask and sells fill at the bid, so a flat round trip loses
    the spread. The half-spread is applied around the requested mid price when
    an explicit fill price is not derivable from the current quote.
    """

    def __init__(self, default_price: float = 1.1000, half_spread_pips: float = 1.0) -> None:
        now = datetime.now(UTC)
        self.half_spread = half_spread_pips * PIP_SIZE
        self._quote = Quote(
            "EUR_USD",
            bid=default_price - self.half_spread,
            ask=default_price + self.half_spread,
            time=now,
        )
        self._positions: dict[str, Position] = {}

    def set_quote(self, quote: Quote) -> None:
        self._quote = quote

    def get_quote(self, symbol: str) -> Quote:
        if symbol != self._quote.symbol:
            return Quote(
                symbol=symbol,
                bid=self._quote.bid,
                ask=self._quote.ask,
                time=self._quote.time,
            )
        return self._quote

    def _fill_price(self, side: OrderSide, requested_price: float | None) -> float:
        """Resolve the executable fill price for a side.

        Prefer the live quote's ask (buy) or bid (sell). If a price is supplied
        and the quote does not cover it, apply the half-spread to that price.
        """
        quote = self._quote
        if requested_price is None:
            return quote.ask if side == OrderSide.BUY else quote.bid
        # Apply the spread cost around the requested (mid) price.
        if side == OrderSide.BUY:
            return requested_price + self.half_spread
        return requested_price - self.half_spread

    def place_market_order(
        self,
        *,
        symbol: str,
        side: str | OrderSide,
        units: int,
        price: float | None,
        stop_loss: float,
        take_profit: float,
        opened_at: datetime | None = None,
    ) -> OrderResult:
        order_side = side if isinstance(side, OrderSide) else OrderSide(side)
        opened = opened_at or datetime.now(UTC)
        fill_price = self._fill_price(order_side, price)
        position_id = new_id("pos")
        order = OrderResult(
            order_id=new_id("ord"),
            position_id=position_id,
            accepted=True,
            reason="Simulated fill accepted.",
            symbol=symbol,
            side=order_side,
            units=units,
            fill_price=fill_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            opened_at=opened,
        )
        self._positions[position_id] = Position(
            position_id=position_id,
            symbol=symbol,
            side=order_side,
            units=units,
            entry_price=fill_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            opened_at=opened,
        )
        return order

    def list_open_positions(self) -> list[Position]:
        return [
            position
            for position in self._positions.values()
            if position.status == PositionStatus.OPEN
        ]

    def close_position(
        self,
        position_id: str,
        price: float | None,
        closed_at: datetime | None = None,
    ) -> Position:
        position = self._positions[position_id]
        # Exiting a long means selling (receive bid); exiting a short means
        # buying (pay ask). Resolve the exit price accordingly.
        exit_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
        exit_price = self._fill_price(exit_side, price)
        return position.close(price=exit_price, closed_at=closed_at or datetime.now(UTC))

    def close_position_at(
        self,
        position_id: str,
        exact_price: float,
        closed_at: datetime | None = None,
    ) -> Position:
        """Close at an exact price with no spread adjustment.

        Used for stop-loss/take-profit fills, where the level itself is already
        the realistic execution price and applying a spread would double-count.
        """
        position = self._positions[position_id]
        return position.close(price=exact_price, closed_at=closed_at or datetime.now(UTC))
