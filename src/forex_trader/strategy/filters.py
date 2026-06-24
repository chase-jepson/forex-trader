from __future__ import annotations

from forex_trader.domain.models import PIP_SIZE, Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class TrendFilter(Strategy):
    """Suppress the inner strategy's signal on strongly trending days.

    Naive entries bleed when a strong directional day runs the stop. If the net
    move over the lookback exceeds `max_trend_pips`, the day is trending and we
    skip the trade. Deterministic — no LLM at runtime.
    """

    def __init__(self, *, inner: Strategy, lookback: int = 6, max_trend_pips: float = 12.0) -> None:
        self.inner = inner
        self.lookback = lookback
        self.max_trend_pips = max_trend_pips
        self.strategy_id = f"trendfilt({inner.strategy_id})"
        self.required_history = max(getattr(inner, "required_history", 2), lookback + 1)

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if len(candles) > self.lookback:
            window = candles[-(self.lookback + 1) :]
            net_pips = abs(window[-1].close - window[0].close) / PIP_SIZE
            if net_pips > self.max_trend_pips:
                return None
        return self.inner.evaluate(candles, quote)


class VolatilityRegimeFilter(Strategy):
    """Suppress the inner signal when the window is too quiet or too wild.

    Trades only when average candle range over the lookback sits within
    [min_avg_range_pips, max_avg_range_pips] — a tradeable volatility regime.
    """

    def __init__(
        self,
        *,
        inner: Strategy,
        lookback: int = 6,
        min_avg_range_pips: float = 4.0,
        max_avg_range_pips: float = 100.0,
    ) -> None:
        self.inner = inner
        self.lookback = lookback
        self.min_avg_range_pips = min_avg_range_pips
        self.max_avg_range_pips = max_avg_range_pips
        self.strategy_id = f"volfilt({inner.strategy_id})"
        self.required_history = max(getattr(inner, "required_history", 2), lookback + 1)

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if len(candles) >= self.lookback:
            window = candles[-self.lookback :]
            avg_range = sum((c.high - c.low) for c in window) / len(window) / PIP_SIZE
            if not (self.min_avg_range_pips <= avg_range <= self.max_avg_range_pips):
                return None
        return self.inner.evaluate(candles, quote)
