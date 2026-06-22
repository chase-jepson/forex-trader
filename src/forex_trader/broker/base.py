from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import OrderResult, Position, Quote


class Broker(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        raise NotImplementedError

    @abstractmethod
    def place_market_order(
        self,
        *,
        symbol: str,
        side: str | OrderSide,
        units: int,
        price: float | None,
        stop_loss: float,
        take_profit: float,
        opened_at: datetime,
    ) -> OrderResult:
        raise NotImplementedError

    @abstractmethod
    def list_open_positions(self) -> list[Position]:
        raise NotImplementedError

    @abstractmethod
    def close_position(
        self, position_id: str, price: float | None, closed_at: datetime
    ) -> Position:
        raise NotImplementedError

