from __future__ import annotations

from collections import defaultdict
from typing import Any

from forex_trader.domain.models import PIP_SIZE, Candle


def _group_by_day(candles: list[Candle]) -> dict[str, list[Candle]]:
    by_day: dict[str, list[Candle]] = defaultdict(list)
    for candle in candles:
        by_day[candle.time.date().isoformat()].append(candle)
    return by_day


def analyze_window(candles: list[Candle]) -> dict[str, Any]:
    """Compute deterministic stats over session candles.

    These describe the market's behavior in the window — average range, net
    directional bias, how often a day closes up, and the breakout
    follow-through rate — so trading rules can be proposed from evidence rather
    than guesswork.
    """
    if not candles:
        return {"candle_count": 0}

    ranges = [(c.high - c.low) / PIP_SIZE for c in candles]
    avg_range = sum(ranges) / len(ranges)
    net_move = candles[-1].close - candles[0].close

    by_day = _group_by_day(candles)
    up_days = sum(
        1 for day in by_day.values() if day[-1].close > day[0].open
    )
    day_count = len(by_day)

    # Breakout follow-through: after a candle closes above the prior candle's
    # high, does the next candle continue up? (and symmetrically for downside)
    cont = _breakout_follow_through(candles)

    return {
        "candle_count": len(candles),
        "day_count": day_count,
        "avg_range_pips": round(avg_range, 2),
        "net_move_pips": round(net_move / PIP_SIZE, 2),
        "directional_bias": "up" if net_move > 0 else "down" if net_move < 0 else "flat",
        "up_day_rate": round(up_days / day_count, 3) if day_count else 0.0,
        "breakout_follow_through_rate": cont,
    }


def _breakout_follow_through(candles: list[Candle]) -> float:
    """Fraction of upside breakouts that continue higher on the next candle."""
    breakouts = 0
    continued = 0
    for i in range(1, len(candles) - 1):
        if candles[i].close > candles[i - 1].high:  # upside breakout
            breakouts += 1
            if candles[i + 1].close > candles[i].close:
                continued += 1
    return round(continued / breakouts, 3) if breakouts else 0.0
