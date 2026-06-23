"""Equity curve built from persisted trade stories."""
from forex_trader.dashboard.equity import build_equity_curve


def _trade(opened, pnl, outcome="win"):
    return {"opened_at": opened, "closed_at": opened, "pnl": pnl, "outcome": outcome}


def test_equity_curve_accumulates_pnl_in_time_order():
    trades = [
        _trade("2026-06-22T12:00:00+00:00", 10.0),
        _trade("2026-06-22T13:00:00+00:00", -4.0, "loss"),
        _trade("2026-06-22T14:00:00+00:00", 6.0),
    ]

    curve = build_equity_curve(trades, starting_equity=1000.0)

    # Starting point plus one per closed trade.
    assert curve["equity"] == [1000.0, 1010.0, 1006.0, 1012.0]
    assert len(curve["times"]) == 4


def test_equity_curve_ignores_open_trades():
    trades = [
        _trade("2026-06-22T12:00:00+00:00", 10.0),
        {"opened_at": "2026-06-22T13:00:00+00:00", "closed_at": None,
         "pnl": None, "outcome": "open"},
    ]

    curve = build_equity_curve(trades, starting_equity=1000.0)

    assert curve["equity"] == [1000.0, 1010.0]  # open trade excluded


def test_equity_curve_empty_is_just_starting_point():
    curve = build_equity_curve([], starting_equity=500.0)
    assert curve["equity"] == [500.0]
