"""Enrich trade stories with the candle window spanning entry through exit."""
from datetime import UTC, datetime, timedelta

from forex_trader.backtest.enrich import enrich_story_candles
from forex_trader.domain.models import Candle


def _series(n):
    start = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    return [
        Candle(time=start + timedelta(minutes=i), open=1.10 + i * 0.0001,
               high=1.101 + i * 0.0001, low=1.099 + i * 0.0001, close=1.10 + i * 0.0001)
        for i in range(n)
    ]


def test_enrich_includes_candles_before_and_through_exit():
    candles = _series(60)
    story = {
        "opened_at": candles[20].time.isoformat(),
        "closed_at": candles[40].time.isoformat(),
        "context_candles": [],
    }

    enriched = enrich_story_candles(story, candles, pad_before=5)

    times = [c["time"] for c in enriched["context_candles"]]
    # Spans from 5 before entry (index 15) through exit (index 40).
    assert times[0] == candles[15].time.isoformat()
    assert times[-1] == candles[40].time.isoformat()
    assert len(times) == 26


def test_enrich_open_trade_runs_to_end_of_series():
    candles = _series(30)
    story = {
        "opened_at": candles[10].time.isoformat(),
        "closed_at": None,
        "context_candles": [],
    }

    enriched = enrich_story_candles(story, candles, pad_before=2)

    times = [c["time"] for c in enriched["context_candles"]]
    assert times[0] == candles[8].time.isoformat()
    assert times[-1] == candles[-1].time.isoformat()
