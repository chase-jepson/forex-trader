from __future__ import annotations

from typing import Any

from forex_trader.dashboard.equity import build_equity_curve, build_equity_figure
from forex_trader.dashboard.performance import (
    build_daily_performance,
    build_daily_pnl_figure,
    build_rolling_win_rate_figure,
)


def render_reports(st: Any, snapshot: dict[str, Any]) -> None:
    st.subheader("Reports")

    reports = snapshot["reports"]
    cols = st.columns(4)
    cols[0].metric("Trades closed", reports.get("trades_closed", 0))
    cols[1].metric("Win rate", f"{reports.get('win_rate', 0.0) * 100:.1f}%")
    cols[2].metric("Realized PnL", f"${reports.get('realized_pnl', 0.0):.2f}")
    cols[3].metric(
        "Avg hold (min)", f"{reports.get('average_hold_minutes', 0.0):.0f}"
    )

    trades = snapshot.get("trades", [])
    if not trades:
        st.info("No trades yet. Run `forex-trader seed` or a dry run to populate.")
        with st.expander("Raw report metrics"):
            st.json(reports)
        return

    # Performance over time — are we getting better or worse?
    st.markdown("#### Are we improving over time?")
    daily = build_daily_performance(trades)
    if daily["days"]:
        first_half_wr, second_half_wr = _split_win_rate(daily["win_rate"])
        trend_cols = st.columns(3)
        trend_cols[0].metric("Trading days", len(daily["days"]))
        trend_cols[1].metric("First-half win rate", f"{first_half_wr:.1f}%")
        trend_cols[2].metric(
            "Second-half win rate", f"{second_half_wr:.1f}%",
            delta=f"{second_half_wr - first_half_wr:+.1f} pts",
        )
        st.plotly_chart(build_daily_pnl_figure(daily), use_container_width=True)

    st.plotly_chart(
        build_rolling_win_rate_figure(trades, window=20), use_container_width=True
    )

    curve = build_equity_curve(trades)
    st.plotly_chart(build_equity_figure(curve), use_container_width=True)

    with st.expander("Raw report metrics"):
        st.json(reports)


def _split_win_rate(win_rates: list[float]) -> tuple[float, float]:
    """Average win rate over the first vs second half of trading days."""
    if not win_rates:
        return 0.0, 0.0
    mid = len(win_rates) // 2 or 1
    first = win_rates[:mid]
    second = win_rates[mid:] or first
    return sum(first) / len(first), sum(second) / len(second)
