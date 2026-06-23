from __future__ import annotations

from typing import Any

import plotly.graph_objects as go


def build_trade_chart(view: dict[str, Any]) -> go.Figure:
    """Build a candlestick chart for a trade story with annotated levels.

    Renders the pre-entry candle window, the entry and (if closed) exit markers,
    and horizontal stop-loss / take-profit lines so the trade's reasoning and
    outcome are visible at a glance.
    """
    candles = view.get("candles", [])
    times = [c["time"] for c in candles]

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=times,
                open=[c["open"] for c in candles],
                high=[c["high"] for c in candles],
                low=[c["low"] for c in candles],
                close=[c["close"] for c in candles],
                name="EUR/USD",
            )
        ]
    )

    # Entry marker.
    fig.add_trace(
        go.Scatter(
            x=[view["entry_time"]],
            y=[view["entry_price"]],
            mode="markers",
            marker={"symbol": "triangle-up" if view["side"] == "buy" else "triangle-down",
                    "size": 14, "color": "#2563eb"},
            name="entry",
        )
    )

    # Exit marker when the trade has closed.
    if view.get("is_closed") and view.get("exit_price") is not None:
        won = view.get("outcome") == "win"
        fig.add_trace(
            go.Scatter(
                x=[view.get("exit_time")],
                y=[view["exit_price"]],
                mode="markers",
                marker={"symbol": "x", "size": 14,
                        "color": "#16a34a" if won else "#dc2626"},
                name="exit",
            )
        )

    # Stop-loss and take-profit as horizontal lines.
    fig.add_hline(y=view["stop_loss"], line={"color": "#dc2626", "dash": "dash"},
                  annotation_text="stop")
    fig.add_hline(y=view["take_profit"], line={"color": "#16a34a", "dash": "dash"},
                  annotation_text="target")

    fig.update_layout(
        title=f"Trade {view['position_id']} ({view['side']})",
        xaxis_rangeslider_visible=False,
        height=480,
    )
    return fig
