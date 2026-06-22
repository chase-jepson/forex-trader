from __future__ import annotations

from abc import ABC, abstractmethod

from forex_trader.domain.models import Candle, Quote, Signal


class Strategy(ABC):
    strategy_id: str

    @abstractmethod
    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        raise NotImplementedError

