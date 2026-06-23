from __future__ import annotations

from typing import Any

from forex_trader.config import Settings
from forex_trader.dashboard.sections.live_market import render_live_market
from forex_trader.dashboard.sections.reports import render_reports
from forex_trader.dashboard.sections.trade_reviews import render_trade_reviews
from forex_trader.dashboard.trade_chart import build_trade_chart
from forex_trader.dashboard.trade_story_view import build_story_view
from forex_trader.reporting.metrics import summarize_trade_outcomes
from forex_trader.storage.repositories import TradingRepository


def build_dashboard_snapshot(
    *,
    quote: dict[str, Any] | None,
    cycles: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    trades: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    latest_cycle = cycles[-1] if cycles else {}
    return {
        "live_market": {
            "symbol": None if quote is None else quote.get("symbol"),
            "bid": None if quote is None else quote.get("bid"),
            "ask": None if quote is None else quote.get("ask"),
            "latest_status": latest_cycle.get("status", "idle"),
            "latest_reason": latest_cycle.get("reason", "No cycle has run yet."),
        },
        "reviews": reviews,
        "reports": summarize_trade_outcomes(reviews),
        "trades": trades or [],
    }


def load_dashboard_snapshot(
    *,
    repository: TradingRepository,
    quote: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a dashboard snapshot from persisted cycles, reviews, and trades."""
    return build_dashboard_snapshot(
        quote=quote,
        cycles=repository.list_cycles(),
        reviews=repository.list_reviews(),
        trades=repository.list_trade_stories(),
    )


def _trade_label(trade: dict[str, Any]) -> str:
    tag = " [dry-run]" if trade.get("is_dry_run") else ""
    outcome = trade.get("outcome", "open")
    pnl = trade.get("pnl")
    pnl_text = "" if pnl is None else f" ${pnl:.2f}"
    return f"{trade['opened_at']} · {trade['side']} · {outcome}{pnl_text}{tag}"


def render_trade_explorer(st: Any, snapshot: dict[str, Any]) -> None:
    """Click a trade → see its chart, the signal reasoning, and its lifecycle."""
    st.subheader("Trade Explorer")
    trades = snapshot.get("trades", [])
    if not trades:
        st.info(
            "No trades recorded yet. Run a backtest into the database "
            "(`forex-trader seed`) or a dry run to populate this view."
        )
        return

    labels = [_trade_label(t) for t in trades]
    # Most recent first for convenience.
    order = list(range(len(trades)))[::-1]
    choice = st.selectbox(
        "Select a trade", order, format_func=lambda i: labels[i]
    )
    trade = trades[choice]
    view = build_story_view(trade)

    st.markdown(f"**What the agent saw:** {view['summary']}")
    cols = st.columns(4)
    cols[0].metric("Entry", f"{view['entry_price']:.5f}")
    cols[1].metric("Stop", f"{view['stop_loss']:.5f}")
    cols[2].metric("Target", f"{view['take_profit']:.5f}")
    cols[3].metric("Outcome", view["outcome"])

    st.plotly_chart(build_trade_chart(view), use_container_width=True)
    with st.expander("Signal metadata & risk decision"):
        st.json(
            {
                "signal_metadata": trade.get("signal_metadata", {}),
                "risk_reason": trade.get("risk_reason", ""),
                "exit_reason": trade.get("exit_reason"),
                "is_dry_run": trade.get("is_dry_run", False),
            }
        )


def main() -> None:
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:
        raise SystemExit("Install dashboard dependencies with `pip install -e .` first.") from exc

    settings = Settings.from_env()
    repository = TradingRepository(settings.database_path)

    st.set_page_config(page_title="Forex Trader", layout="wide")
    st.title("EUR/USD Trading Console")
    st.caption(f"Local-first {settings.app_mode} console with rule explanations and reviews.")

    snapshot = load_dashboard_snapshot(repository=repository)
    render_live_market(st, snapshot)
    render_trade_explorer(st, snapshot)
    render_trade_reviews(st, snapshot)
    render_reports(st, snapshot)


if __name__ == "__main__":
    main()
