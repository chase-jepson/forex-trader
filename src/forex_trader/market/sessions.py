from __future__ import annotations

from datetime import datetime, time


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":", maxsplit=1)
    return time(hour=int(hour), minute=int(minute))


def can_open_new_trade(now: datetime, session_start_local: str, session_end_local: str) -> bool:
    start = parse_hhmm(session_start_local)
    end = parse_hhmm(session_end_local)
    current = now.timetz().replace(tzinfo=None)
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def must_close_position(
    opened_at: datetime,
    now: datetime,
    max_hold_minutes: int,
    session_end_local: str,
) -> bool:
    held_minutes = (now - opened_at).total_seconds() / 60
    if held_minutes >= max_hold_minutes:
        return True
    current = now.timetz().replace(tzinfo=None)
    return current >= parse_hhmm(session_end_local)

