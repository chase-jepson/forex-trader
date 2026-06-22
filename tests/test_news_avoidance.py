"""News avoidance: suppress an inner strategy's signals near high-impact events."""
from datetime import UTC, datetime, timedelta

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote, Signal
from forex_trader.strategy.base import Strategy
from forex_trader.strategy.news_avoidance import (
    NewsAvoidanceStrategy,
    NewsEvent,
)


class _AlwaysBuy(Strategy):
    strategy_id = "always_buy"

    def evaluate(self, candles, quote):
        return Signal(
            strategy_id=self.strategy_id, symbol="EUR_USD", side=OrderSide.BUY,
            entry_price=1.1000, stop_loss=1.0990, take_profit=1.1020, reason="test",
        )


def _inputs(now):
    candles = [Candle(time=now, open=1.1, high=1.1, low=1.1, close=1.1)]
    return candles, Quote(symbol="EUR_USD", bid=1.0999, ask=1.1001, time=now)


def test_suppresses_signal_within_blackout_window():
    event_time = datetime(2026, 6, 22, 12, 30, tzinfo=UTC)
    strat = NewsAvoidanceStrategy(
        inner=_AlwaysBuy(),
        events=[NewsEvent(time=event_time, severity="high")],
        blackout_minutes=15,
    )
    now = datetime(2026, 6, 22, 12, 20, tzinfo=UTC)  # 10 min before -> within 15-min blackout
    candles, quote = _inputs(now)

    assert strat.evaluate(candles, quote) is None


def test_allows_signal_outside_blackout_window():
    event_time = datetime(2026, 6, 22, 12, 30, tzinfo=UTC)
    strat = NewsAvoidanceStrategy(
        inner=_AlwaysBuy(),
        events=[NewsEvent(time=event_time, severity="high")],
        blackout_minutes=15,
    )
    now = datetime(2026, 6, 22, 11, 0, tzinfo=UTC)  # 90 min before -> clear
    candles, quote = _inputs(now)

    signal = strat.evaluate(candles, quote)
    assert signal is not None
    assert signal.side == OrderSide.BUY


def test_ignores_low_severity_events():
    event_time = datetime(2026, 6, 22, 12, 30, tzinfo=UTC)
    strat = NewsAvoidanceStrategy(
        inner=_AlwaysBuy(),
        events=[NewsEvent(time=event_time, severity="low")],
        blackout_minutes=15,
    )
    now = event_time - timedelta(minutes=5)
    candles, quote = _inputs(now)

    # Low severity should not trigger a blackout.
    assert strat.evaluate(candles, quote) is not None
