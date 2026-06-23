from __future__ import annotations

from abc import ABC, abstractmethod

from forex_trader.domain.models import Candle, Quote, Signal


class Strategy(ABC):
    strategy_id: str

    # Minimum number of candles the strategy needs to evaluate. The backtest /
    # live window is sized to cover this so the strategy always has enough data.
    required_history: int = 2

    @abstractmethod
    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        raise NotImplementedError

