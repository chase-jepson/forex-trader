"""Candle feed: load from CSV and generate synthetic candles."""
from datetime import UTC, datetime

from forex_trader.backtest.feed import (
    generate_synthetic_candles,
    load_candles_csv,
)


def test_load_candles_csv_parses_ohlc(tmp_path):
    csv = tmp_path / "candles.csv"
    csv.write_text(
        "time,open,high,low,close\n"
        "2026-06-22T12:00:00+00:00,1.1000,1.1010,1.0995,1.1005\n"
        "2026-06-22T12:01:00+00:00,1.1005,1.1020,1.1002,1.1018\n"
    )

    candles = load_candles_csv(csv)

    assert len(candles) == 2
    assert candles[0].open == 1.1000
    assert candles[0].close == 1.1005
    assert candles[1].high == 1.1020
    assert candles[0].time == datetime(2026, 6, 22, 12, 0, tzinfo=UTC)


def test_generate_synthetic_candles_is_deterministic_for_a_seed():
    start = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)

    a = generate_synthetic_candles(start=start, count=50, seed=7)
    b = generate_synthetic_candles(start=start, count=50, seed=7)

    assert len(a) == 50
    assert [c.close for c in a] == [c.close for c in b]  # same seed -> same series


def test_generate_synthetic_candles_have_consistent_ohlc():
    start = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)

    candles = generate_synthetic_candles(start=start, count=100, seed=1)

    for c in candles:
        assert c.high >= c.open
        assert c.high >= c.close
        assert c.low <= c.open
        assert c.low <= c.close
        assert c.high >= c.low
