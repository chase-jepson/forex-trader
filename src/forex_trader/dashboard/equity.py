from __future__ import annotations

from typing import Any

import plotly.graph_objects as go


def build_equity_curve(
    trades: list[dict[str, Any]], *, starting_equity: float = 10_000.0
) -> dict[str, list[Any]]:
    """Accumulate realized PnL over closed trades, in close-time order.

    Returns parallel `times` and `equity` lists, beginning with the starting
    equity. Open trades (no close, no pnl) are excluded.
    """
    closed = [
        t for t in trades if t.get("closed_at") and t.get("pnl") is not None
    ]
    closed.sort(key=lambda t: t["closed_at"])

    times: list[Any] = ["start"]
    equity = [starting_equity]
    running = starting_equity
    for trade in closed:
        running += float(trade["pnl"])
        times.append(trade["closed_at"])
        equity.append(round(running, 2))
    return {"times": times, "equity": equity}


def build_equity_figure(curve: dict[str, list[Any]]) -> go.Figure:
    """Render the equity curve against close time (real datetimes)."""
    times = curve["times"]
    # The first point is the "start" sentinel; substitute the first real close
    # time (or a label) so the x-axis is a clean datetime series.
    x = list(times)
    if len(x) > 1 and x[0] == "start":
        x[0] = times[1]
    fig = go.Figure(
        data=[
            go.Scatter(
                x=x,
                y=curve["equity"],
                mode="lines",
                line={"color": "#2563eb"},
                name="equity",
            )
        ]
    )
    fig.update_layout(
        title="Equity curve over time (realized)",
        xaxis_title="close time",
        yaxis_title="equity",
        height=320,
    )
    return fig
