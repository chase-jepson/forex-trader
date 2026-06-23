from __future__ import annotations

from datetime import datetime
from typing import Any

from forex_trader.domain.models import Candle


def _to_dict(candle: Candle) -> dict[str, Any]:
    return {
        "time": candle.time.isoformat(),
        "open": candle.open,
        "high": candle.high,
        "low": candle.low,
        "close": candle.close,
    }


def enrich_story_candles(
    story: dict[str, Any],
    candles: list[Candle],
    *,
    pad_before: int = 10,
) -> dict[str, Any]:
    """Return a copy of `story` whose context_candles span entry through exit.

    Includes `pad_before` candles before the entry so the setup is visible, then
    every candle up to the exit (or the end of the series for an open trade), so
    the trade can be watched unfolding through time.
    """
    opened_at = datetime.fromisoformat(story["opened_at"])
    closed_raw = story.get("closed_at")
    closed_at = datetime.fromisoformat(closed_raw) if closed_raw else None

    entry_index = _first_index_at_or_after(candles, opened_at)
    if entry_index is None:
        return {**story, "context_candles": [_to_dict(c) for c in candles]}

    start = max(0, entry_index - pad_before)
    if closed_at is None:
        end = len(candles) - 1
    else:
        exit_index = _first_index_at_or_after(candles, closed_at)
        end = len(candles) - 1 if exit_index is None else exit_index

    window = candles[start : end + 1]
    return {**story, "context_candles": [_to_dict(c) for c in window]}


def _first_index_at_or_after(candles: list[Candle], when: datetime) -> int | None:
    for index, candle in enumerate(candles):
        if candle.time >= when:
            return index
    return None
