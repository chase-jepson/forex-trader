"""Build a chart-ready view model from a stored trade story."""
from forex_trader.dashboard.trade_story_view import build_story_view


def _story(outcome="win"):
    return {
        "position_id": "pos-1",
        "opened_at": "2026-06-22T12:00:00+00:00",
        "side": "buy",
        "entry_price": 1.1016,
        "stop_loss": 1.0990,
        "take_profit": 1.1060,
        "units": 25000,
        "signal_reason": "Broke above the opening range.",
        "signal_metadata": {"opening_high": 1.1020, "opening_low": 1.0990},
        "risk_reason": "Approved within risk.",
        "context_candles": [
            {"time": "2026-06-22T11:55:00+00:00", "open": 1.10, "high": 1.101,
             "low": 1.099, "close": 1.1005},
            {"time": "2026-06-22T11:56:00+00:00", "open": 1.1005, "high": 1.102,
             "low": 1.10, "close": 1.1015},
        ],
        "is_dry_run": False,
        "closed_at": "2026-06-22T12:45:00+00:00",
        "close_price": 1.1060,
        "outcome": outcome,
        "pnl": 110.0,
        "exit_reason": "take_profit",
    }


def test_view_exposes_levels_and_markers():
    view = build_story_view(_story())

    assert view["entry_price"] == 1.1016
    assert view["stop_loss"] == 1.0990
    assert view["take_profit"] == 1.1060
    assert view["entry_time"] == "2026-06-22T12:00:00+00:00"
    assert view["exit_time"] == "2026-06-22T12:45:00+00:00"
    assert view["exit_price"] == 1.1060
    assert view["is_closed"] is True
    assert len(view["candles"]) == 2


def test_view_summary_explains_the_trade():
    view = build_story_view(_story())

    assert "buy" in view["summary"].lower()
    assert "opening range" in view["summary"].lower()
    assert "take_profit" in view["summary"].lower()


def test_open_trade_view_has_no_exit():
    story = _story()
    story["closed_at"] = None
    story["close_price"] = None
    story["outcome"] = "open"

    view = build_story_view(story)

    assert view["is_closed"] is False
    assert view["exit_time"] is None
