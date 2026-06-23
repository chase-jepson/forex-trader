"""Time-based performance: equity over datetime + daily win-rate/PnL trend."""
from forex_trader.dashboard.performance import (
    build_daily_performance,
    rolling_win_rate,
)


def _trade(closed_at, pnl, outcome):
    return {"closed_at": closed_at, "pnl": pnl, "outcome": outcome,
            "opened_at": closed_at}


def test_daily_performance_groups_by_calendar_day():
    trades = [
        _trade("2026-06-22T10:00:00+00:00", 10.0, "win"),
        _trade("2026-06-22T14:00:00+00:00", -4.0, "loss"),
        _trade("2026-06-23T09:00:00+00:00", 6.0, "win"),
    ]

    daily = build_daily_performance(trades)

    assert daily["days"] == ["2026-06-22", "2026-06-23"]
    assert daily["pnl"] == [6.0, 6.0]            # 10-4, then 6
    assert daily["win_rate"] == [50.0, 100.0]    # 1/2, then 1/1
    assert daily["trades"] == [2, 1]
    assert daily["cumulative_pnl"] == [6.0, 12.0]


def test_daily_performance_empty():
    daily = build_daily_performance([])
    assert daily["days"] == []


def test_rolling_win_rate_uses_a_window():
    # 5 trades: W W L W W -> rolling(window=3) at each step.
    trades = [
        _trade("2026-06-22T01:00:00+00:00", 1, "win"),
        _trade("2026-06-22T02:00:00+00:00", 1, "win"),
        _trade("2026-06-22T03:00:00+00:00", -1, "loss"),
        _trade("2026-06-22T04:00:00+00:00", 1, "win"),
        _trade("2026-06-22T05:00:00+00:00", 1, "win"),
    ]

    rates = rolling_win_rate(trades, window=3)

    # windows: [W]=100, [W,W]=100, [W,W,L]=66.7, [W,L,W]=66.7, [L,W,W]=66.7
    assert rates[0] == 100.0
    assert round(rates[2], 1) == 66.7
    assert round(rates[-1], 1) == 66.7
