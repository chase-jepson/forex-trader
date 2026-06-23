"""Filter candles to a daily local session window (US-open)."""
from datetime import UTC, datetime

from forex_trader.backtest.session_filter import filter_session_window
from forex_trader.domain.models import Candle


def _c(dt):
    return Candle(time=dt, open=1.1, high=1.1, low=1.1, close=1.1)


def test_keeps_only_candles_inside_us_open_window():
    # US-open window 08:30-11:30 America/New_York. In June, ET = UTC-4.
    # 08:30 ET = 12:30 UTC; 11:30 ET = 15:30 UTC.
    candles = [
        _c(datetime(2026, 6, 1, 11, 0, tzinfo=UTC)),   # 07:00 ET — before, drop
        _c(datetime(2026, 6, 1, 12, 30, tzinfo=UTC)),  # 08:30 ET — keep (start)
        _c(datetime(2026, 6, 1, 14, 0, tzinfo=UTC)),   # 10:00 ET — keep
        _c(datetime(2026, 6, 1, 15, 30, tzinfo=UTC)),  # 11:30 ET — keep (end)
        _c(datetime(2026, 6, 1, 16, 0, tzinfo=UTC)),   # 12:00 ET — after, drop
    ]

    kept = filter_session_window(
        candles, tz="America/New_York", start_hhmm="08:30", end_hhmm="11:30"
    )

    assert len(kept) == 3
    assert kept[0].time == datetime(2026, 6, 1, 12, 30, tzinfo=UTC)
    assert kept[-1].time == datetime(2026, 6, 1, 15, 30, tzinfo=UTC)


def test_window_applies_per_day_across_multiple_days():
    candles = [
        _c(datetime(2026, 6, 1, 13, 0, tzinfo=UTC)),  # day1 in-window
        _c(datetime(2026, 6, 1, 20, 0, tzinfo=UTC)),  # day1 out
        _c(datetime(2026, 6, 2, 13, 0, tzinfo=UTC)),  # day2 in-window
    ]

    kept = filter_session_window(
        candles, tz="America/New_York", start_hhmm="08:30", end_hhmm="11:30"
    )

    assert len(kept) == 2
    assert {k.time.day for k in kept} == {1, 2}
