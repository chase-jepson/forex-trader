from __future__ import annotations

from datetime import time
from zoneinfo import ZoneInfo

from forex_trader.domain.models import Candle

# US equity-market open window: 1 hour before the 09:30 ET open through 2 hours
# after — the most volatile, tradeable part of the EUR/USD day.
US_OPEN_TZ = "America/New_York"
US_OPEN_START = "08:30"
US_OPEN_END = "11:30"


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":", maxsplit=1)
    return time(hour=int(hour), minute=int(minute))


def filter_session_window(
    candles: list[Candle],
    *,
    tz: str = US_OPEN_TZ,
    start_hhmm: str = US_OPEN_START,
    end_hhmm: str = US_OPEN_END,
) -> list[Candle]:
    """Keep only candles whose local time falls within [start, end] each day.

    Each candle's UTC time is converted to the session timezone before the
    comparison, so daylight-saving shifts are handled correctly.
    """
    zone = ZoneInfo(tz)
    start = _parse_hhmm(start_hhmm)
    end = _parse_hhmm(end_hhmm)
    kept: list[Candle] = []
    for candle in candles:
        local = candle.time.astimezone(zone).time()
        if start <= local <= end:
            kept.append(candle)
    return kept
