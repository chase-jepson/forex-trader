from datetime import UTC, datetime, timedelta

from forex_trader.config import Settings
from forex_trader.market.sessions import can_open_new_trade, must_close_position


def test_settings_defaults_are_simulated_eurusd_and_conservative():
    settings = Settings()

    assert settings.app_mode == "simulated"
    assert settings.trade_symbol == "EUR_USD"
    assert settings.max_risk_per_trade == 0.0025
    assert settings.max_open_positions == 1


def test_trade_window_allows_entries_inside_session():
    now = datetime.fromisoformat("2026-06-22T05:30:00-06:00")

    assert can_open_new_trade(now, "05:00", "09:00") is True


def test_trade_window_blocks_entries_after_cutoff():
    now = datetime.fromisoformat("2026-06-22T09:01:00-06:00")

    assert can_open_new_trade(now, "05:00", "09:00") is False


def test_position_must_close_after_max_hold_time():
    opened_at = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    now = opened_at + timedelta(minutes=91)

    assert must_close_position(opened_at, now, max_hold_minutes=90, session_end_local="23:59")

