from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

DEFAULT_SESSION_TZ = "America/Mexico_City"


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":", maxsplit=1)
    return time(hour=int(hour), minute=int(minute))


def _local_time(now: datetime, session_tz: str) -> time:
    """Return the wall-clock time of `now` in the session timezone.

    `now` is expected to be timezone-aware (UTC in practice). A naive datetime
    is assumed to already be in the session timezone.
    """
    if now.tzinfo is None:
        return now.time()
    return now.astimezone(ZoneInfo(session_tz)).time()


def can_open_new_trade(
    now: datetime,
    session_start_local: str,
    session_end_local: str,
    session_tz: str = DEFAULT_SESSION_TZ,
) -> bool:
    start = parse_hhmm(session_start_local)
    end = parse_hhmm(session_end_local)
    current = _local_time(now, session_tz)
    if start <= end:
        return start <= current <= end
    # Window wraps past midnight.
    return current >= start or current <= end


def must_close_position(
    opened_at: datetime,
    now: datetime,
    max_hold_minutes: int,
    session_end_local: str,
    session_tz: str = DEFAULT_SESSION_TZ,
) -> bool:
    held_minutes = (now - opened_at).total_seconds() / 60
    if held_minutes >= max_hold_minutes:
        return True
    current = _local_time(now, session_tz)
    return current >= parse_hhmm(session_end_local)
