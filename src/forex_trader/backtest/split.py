from __future__ import annotations

from datetime import datetime

from forex_trader.domain.models import Candle


def split_by_date(
    candles: list[Candle], *, split: datetime
) -> tuple[list[Candle], list[Candle]]:
    """Partition candles into (in_sample < split, out_of_sample >= split).

    The in-sample set is used to find and optimize rules; the out-of-sample set
    is held back to validate that the rules generalize (not curve-fit).
    """
    in_sample = [c for c in candles if c.time < split]
    out_sample = [c for c in candles if c.time >= split]
    return in_sample, out_sample


def midpoint_date(candles: list[Candle]) -> datetime:
    """The time exactly halfway between the first and last candle."""
    if not candles:
        raise ValueError("Cannot find the midpoint of an empty candle series.")
    first = candles[0].time
    last = candles[-1].time
    return first + (last - first) / 2
