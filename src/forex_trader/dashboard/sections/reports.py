from __future__ import annotations

from typing import Any

from forex_trader.dashboard.equity import build_equity_curve, build_equity_figure


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
    if trades:
        curve = build_equity_curve(trades)
        st.plotly_chart(build_equity_figure(curve), use_container_width=True)

    with st.expander("Raw report metrics"):
        st.json(reports)
