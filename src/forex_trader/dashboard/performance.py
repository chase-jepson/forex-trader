from __future__ import annotations

from collections import defaultdict
from typing import Any

import plotly.graph_objects as go


def _closed_sorted(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    closed = [t for t in trades if t.get("closed_at") and t.get("pnl") is not None]
    closed.sort(key=lambda t: t["closed_at"])
    return closed


def build_daily_performance(trades: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """Group closed trades by calendar day (UTC date of close).

    Returns parallel lists for days, per-day pnl, win rate (%), trade count, and
    cumulative pnl — so you can see whether each day is better or worse.
    """
    by_day_pnl: dict[str, float] = defaultdict(float)
    by_day_wins: dict[str, int] = defaultdict(int)
    by_day_count: dict[str, int] = defaultdict(int)

    for trade in _closed_sorted(trades):
        day = str(trade["closed_at"])[:10]  # YYYY-MM-DD
        by_day_pnl[day] += float(trade["pnl"])
        by_day_count[day] += 1
        if trade.get("outcome") == "win":
            by_day_wins[day] += 1

    days = sorted(by_day_pnl)
    pnl = [round(by_day_pnl[d], 2) for d in days]
    trades_per_day = [by_day_count[d] for d in days]
    win_rate = [
        round(100.0 * by_day_wins[d] / by_day_count[d], 1) if by_day_count[d] else 0.0
        for d in days
    ]
    cumulative: list[float] = []
    running = 0.0
    for value in pnl:
        running += value
        cumulative.append(round(running, 2))

    return {
        "days": days,
        "pnl": pnl,
        "win_rate": win_rate,
        "trades": trades_per_day,
        "cumulative_pnl": cumulative,
    }


def rolling_win_rate(trades: list[dict[str, Any]], *, window: int = 20) -> list[float]:
    """Win rate (%) over a trailing window of the last `window` closed trades.

    Lets you see whether recent performance is trending up or down rather than
    just the lifetime average.
    """
    closed = _closed_sorted(trades)
    wins = [1 if t.get("outcome") == "win" else 0 for t in closed]
    rates: list[float] = []
    for i in range(len(wins)):
        start = max(0, i - window + 1)
        chunk = wins[start : i + 1]
        rates.append(round(100.0 * sum(chunk) / len(chunk), 4))
    return rates


def build_daily_pnl_figure(daily: dict[str, list[Any]]) -> go.Figure:
    """Bar chart of per-day PnL (green up / red down) with cumulative line."""
    days = daily["days"]
    pnl = daily["pnl"]
    colors = ["#16a34a" if v >= 0 else "#dc2626" for v in pnl]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=days, y=pnl, marker_color=colors, name="daily PnL"))
    fig.add_trace(
        go.Scatter(
            x=days, y=daily["cumulative_pnl"], mode="lines+markers",
            line={"color": "#2563eb"}, name="cumulative PnL", yaxis="y",
        )
    )
    fig.update_layout(
        title="Daily PnL and cumulative (are we improving?)",
        xaxis_title="day", yaxis_title="PnL", height=340, barmode="overlay",
    )
    return fig


def build_rolling_win_rate_figure(
    trades: list[dict[str, Any]], *, window: int = 20
) -> go.Figure:
    """Line chart of the trailing win rate over close time."""
    closed = _closed_sorted(trades)
    times = [t["closed_at"] for t in closed]
    rates = rolling_win_rate(trades, window=window)
    fig = go.Figure(
        data=[
            go.Scatter(x=times, y=rates, mode="lines", line={"color": "#7c3aed"},
                       name=f"win rate ({window}-trade)")
        ]
    )
    fig.update_layout(
        title=f"Rolling win rate (last {window} trades)",
        xaxis_title="close time", yaxis_title="win rate (%)", height=320,
    )
    return fig
