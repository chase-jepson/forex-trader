from __future__ import annotations

from datetime import datetime

from forex_trader.market.sessions import must_close_position


def should_force_close(
    opened_at: datetime,
    now: datetime,
    max_hold_minutes: int,
    session_end: str,
) -> bool:
    return must_close_position(opened_at, now, max_hold_minutes, session_end)
