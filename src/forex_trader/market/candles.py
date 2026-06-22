from __future__ import annotations

from collections.abc import Iterable

from forex_trader.domain.models import Candle


def latest_close(candles: Iterable[Candle]) -> float | None:
    last: Candle | None = None
    for candle in candles:
        last = candle
    return None if last is None else last.close
