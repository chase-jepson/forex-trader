from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from forex_trader.domain.models import Candle, Quote, Signal
from forex_trader.strategy.base import Strategy

HIGH_IMPACT_SEVERITIES = {"high", "critical"}


@dataclass(frozen=True)
class NewsEvent:
    time: datetime
    severity: str


class NewsAvoidanceStrategy(Strategy):
    """Wrap an inner strategy and suppress signals near high-impact events.

    This is a risk filter, not a signal generator: it delegates to `inner` and
    drops the resulting signal when the candle time falls within
    `blackout_minutes` of any high-impact event. Low-impact events are ignored.
    """

    strategy_id = "eurusd_news_avoidance"

    def __init__(
        self,
        *,
        inner: Strategy,
        events: list[NewsEvent],
        blackout_minutes: int = 30,
    ) -> None:
        self.inner = inner
        self.events = events
        self.blackout = timedelta(minutes=blackout_minutes)

    def _in_blackout(self, when: datetime) -> bool:
        for event in self.events:
            if event.severity.lower() not in HIGH_IMPACT_SEVERITIES:
                continue
            if abs(when - event.time) <= self.blackout:
                return True
        return False

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        when = candles[-1].time if candles else (quote.time if quote else None)
        if when is not None and self._in_blackout(when):
            return None
        return self.inner.evaluate(candles, quote)
