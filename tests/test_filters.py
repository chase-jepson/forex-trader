"""Composable strategy filters: skip trend days, require volatility regime."""
from datetime import UTC, datetime, timedelta

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote, Signal
from forex_trader.strategy.base import Strategy
from forex_trader.strategy.filters import TrendFilter, VolatilityRegimeFilter


class _AlwaysSell(Strategy):
    strategy_id = "always_sell"
    required_history = 2

    def evaluate(self, candles, quote):
        return Signal(strategy_id=self.strategy_id, symbol="EUR_USD",
                      side=OrderSide.SELL, entry_price=1.10, stop_loss=1.101,
                      take_profit=1.099, reason="t")


def _candles(closes):
    start = datetime(2026, 6, 1, 12, 30, tzinfo=UTC)
    return [Candle(time=start + timedelta(minutes=5 * i), open=c, high=c + 0.0001,
                   low=c - 0.0001, close=c) for i, c in enumerate(closes)]


def test_trend_filter_blocks_signal_on_strong_trend():
    inner = _AlwaysSell()
    filt = TrendFilter(inner=inner, lookback=5, max_trend_pips=10.0)
    # Strong uptrend: 25 pips over the lookback -> block the (sell) signal.
    trending = _candles([1.1000, 1.1006, 1.1012, 1.1018, 1.1025, 1.1030])

    assert filt.evaluate(trending, _quote()) is None


def test_trend_filter_allows_signal_in_range():
    inner = _AlwaysSell()
    filt = TrendFilter(inner=inner, lookback=5, max_trend_pips=10.0)
    ranging = _candles([1.1000, 1.1002, 1.0999, 1.1001, 1.1000, 1.1001])

    assert filt.evaluate(ranging, _quote()) is not None


def test_volatility_regime_filter_blocks_when_too_quiet():
    inner = _AlwaysSell()
    filt = VolatilityRegimeFilter(inner=inner, lookback=5, min_avg_range_pips=5.0)
    # Tiny ranges (~2 pips) -> below the 5-pip floor -> block.
    quiet = _candles([1.1000, 1.1001, 1.1000, 1.1001, 1.1000, 1.1001])

    assert filt.evaluate(quiet, _quote()) is None


def _quote():
    return Quote(symbol="EUR_USD", bid=1.0999, ask=1.1001,
                 time=datetime(2026, 6, 1, 12, 55, tzinfo=UTC))
