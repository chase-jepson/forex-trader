"""Deterministic market analysis over session candles."""
from datetime import UTC, datetime, timedelta

from forex_trader.analysis.market import analyze_window
from forex_trader.domain.models import Candle


def _series(closes, start=None):
    start = start or datetime(2026, 6, 1, 12, 30, tzinfo=UTC)
    out = []
    for i, c in enumerate(closes):
        out.append(Candle(time=start + timedelta(minutes=5 * i),
                          open=c, high=c + 0.0005, low=c - 0.0005, close=c))
    return out


def test_analysis_reports_core_stats():
    candles = _series([1.1000, 1.1010, 1.1020, 1.1015, 1.1030])

    stats = analyze_window(candles)

    assert stats["candle_count"] == 5
    assert stats["avg_range_pips"] > 0
    # Net move up over the window -> positive directional bias.
    assert stats["directional_bias"] == "up"
    assert "up_day_rate" in stats
    assert 0.0 <= stats["up_day_rate"] <= 1.0


def test_analysis_handles_empty():
    stats = analyze_window([])
    assert stats["candle_count"] == 0


def test_directional_bias_down():
    candles = _series([1.1030, 1.1020, 1.1010, 1.1000])
    assert analyze_window(candles)["directional_bias"] == "down"
