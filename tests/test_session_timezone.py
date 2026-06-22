"""Session windows are defined in a local timezone but `now` arrives in UTC.

These tests pin that the session helpers convert UTC to the configured
session timezone before comparing against the local HH:MM window.
"""
from datetime import UTC, datetime

from forex_trader.market.sessions import can_open_new_trade, must_close_position


def test_window_uses_session_timezone_not_raw_utc():
    # 12:00 UTC is 06:00 in America/Mexico_City (UTC-6), inside a 05:00-09:00
    # local window. A naive UTC comparison would wrongly reject it (12:00 > 09:00).
    now_utc = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)

    assert can_open_new_trade(
        now_utc, "05:00", "09:00", session_tz="America/Mexico_City"
    ) is True


def test_window_rejects_outside_local_session():
    # 18:00 UTC is 12:00 local (UTC-6), outside the 05:00-09:00 window.
    now_utc = datetime(2026, 6, 22, 18, 0, tzinfo=UTC)

    assert can_open_new_trade(
        now_utc, "05:00", "09:00", session_tz="America/Mexico_City"
    ) is False


def test_must_not_force_close_before_local_cutoff():
    # Opened 12:00 UTC (06:00 local), now 12:30 UTC (06:30 local). Cutoff 09:00
    # local has NOT passed and max hold (90m) not reached -> keep open.
    opened = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    now = datetime(2026, 6, 22, 12, 30, tzinfo=UTC)

    assert must_close_position(
        opened, now, max_hold_minutes=90, session_end_local="09:00",
        session_tz="America/Mexico_City",
    ) is False


def test_must_force_close_after_local_cutoff():
    # Now 15:30 UTC = 09:30 local, past the 09:00 cutoff -> force close.
    opened = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    now = datetime(2026, 6, 22, 15, 30, tzinfo=UTC)

    assert must_close_position(
        opened, now, max_hold_minutes=90, session_end_local="09:00",
        session_tz="America/Mexico_City",
    ) is True
