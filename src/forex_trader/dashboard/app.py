from __future__ import annotations

from typing import Any

from forex_trader.dashboard.pages.live_market import render_live_market
from forex_trader.dashboard.pages.reports import render_reports
from forex_trader.dashboard.pages.trade_reviews import render_trade_reviews
from forex_trader.reporting.metrics import summarize_trade_outcomes


def build_dashboard_snapshot(
    *,
    quote: dict[str, Any] | None,
    cycles: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
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
    }


def main() -> None:
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:
        raise SystemExit("Install dashboard dependencies with `pip install -e .` first.") from exc

    st.set_page_config(page_title="Forex Trader", layout="wide")
    st.title("EUR/USD Trading Console")
    st.caption("Local-first simulator with rule explanations and trade reviews.")
    snapshot = build_dashboard_snapshot(quote=None, cycles=[], reviews=[])
    render_live_market(st, snapshot)
    render_trade_reviews(st, snapshot)
    render_reports(st, snapshot)


if __name__ == "__main__":
    main()
