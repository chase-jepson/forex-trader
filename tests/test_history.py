"""Historical candle sourcing for backtests."""
from datetime import UTC, datetime

from forex_trader.backtest.history import (
    parse_oanda_candles,
    realistic_session_candles,
)


def test_parse_oanda_candles_maps_to_domain_candles():
    payload = {
        "candles": [
            {"time": "2026-06-22T12:00:00.000000000Z", "complete": True,
             "mid": {"o": "1.10000", "h": "1.10050", "l": "1.09990", "c": "1.10030"}},
            {"time": "2026-06-22T12:01:00.000000000Z", "complete": True,
             "mid": {"o": "1.10030", "h": "1.10060", "l": "1.10020", "c": "1.10040"}},
        ]
    }

    candles = parse_oanda_candles(payload)

    assert len(candles) == 2
    assert candles[0].open == 1.10000
    assert candles[0].close == 1.10030
    assert candles[1].high == 1.10060
    assert candles[0].time == datetime(2026, 6, 22, 12, 0, tzinfo=UTC)


def test_parse_oanda_candles_skips_incomplete():
    payload = {
        "candles": [
            {"time": "2026-06-22T12:00:00.000000000Z", "complete": True,
             "mid": {"o": "1.1", "h": "1.1", "l": "1.1", "c": "1.1"}},
            {"time": "2026-06-22T12:01:00.000000000Z", "complete": False,
             "mid": {"o": "1.1", "h": "1.1", "l": "1.1", "c": "1.1"}},
        ]
    }

    candles = parse_oanda_candles(payload)

    assert len(candles) == 1  # incomplete (forming) candle dropped


def test_realistic_session_candles_are_deterministic_and_multiday():
    start = datetime(2026, 6, 22, 0, 0, tzinfo=UTC)

    a = realistic_session_candles(start=start, days=3, seed=4)
    b = realistic_session_candles(start=start, days=3, seed=4)

    assert [c.close for c in a] == [c.close for c in b]
    # Spans multiple calendar days.
    assert len({c.time.date() for c in a}) == 3


def test_realistic_session_candles_have_valid_ohlc():
    start = datetime(2026, 6, 22, 0, 0, tzinfo=UTC)
    candles = realistic_session_candles(start=start, days=2, seed=1)

    for c in candles:
        assert c.high >= max(c.open, c.close)
        assert c.low <= min(c.open, c.close)


def test_candle_source_uses_fixture_when_not_real():
    from forex_trader.backtest.history import resolve_candle_source

    candles = resolve_candle_source(
        use_real=False, token="", days=2, seed=1, granularity="M5", count=500,
    )
    assert len(candles) > 0  # fixture generated, no network


def test_candle_source_real_requires_token():
    import pytest

    from forex_trader.backtest.history import resolve_candle_source

    with pytest.raises(ValueError, match="token"):
        resolve_candle_source(
            use_real=True, token="", days=2, seed=1, granularity="M5", count=500,
        )
