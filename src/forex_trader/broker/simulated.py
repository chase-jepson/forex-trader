from __future__ import annotations

from datetime import UTC, datetime

from forex_trader.broker.base import Broker
from forex_trader.domain.enums import OrderSide, PositionStatus
from forex_trader.domain.models import OrderResult, Position, Quote, new_id


class SimulatedBroker(Broker):
    def __init__(self, default_price: float = 1.1000) -> None:
        now = datetime.now(UTC)
        self._quote = Quote(
            "EUR_USD",
            bid=default_price - 0.0001,
            ask=default_price + 0.0001,
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

    def place_market_order(
        self,
        *,
        symbol: str,
        side: str | OrderSide,
        units: int,
        price: float,
        stop_loss: float,
        take_profit: float,
        opened_at: datetime | None = None,
    ) -> OrderResult:
        order_side = side if isinstance(side, OrderSide) else OrderSide(side)
        opened = opened_at or datetime.now(UTC)
        position_id = new_id("pos")
        order = OrderResult(
            order_id=new_id("ord"),
            position_id=position_id,
            accepted=True,
            reason="Simulated fill accepted.",
            symbol=symbol,
            side=order_side,
            units=units,
            fill_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            opened_at=opened,
        )
        self._positions[position_id] = Position(
            position_id=position_id,
            symbol=symbol,
            side=order_side,
            units=units,
            entry_price=price,
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
        price: float,
        closed_at: datetime | None = None,
    ) -> Position:
        position = self._positions[position_id]
        return position.close(price=price, closed_at=closed_at or datetime.now(UTC))
