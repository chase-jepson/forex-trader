from __future__ import annotations

from forex_trader.domain.models import Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class NullStrategy(Strategy):
    strategy_id = "null"

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        return None

