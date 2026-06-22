from __future__ import annotations

from typing import Any

from forex_trader.reporting.metrics import summarize_trade_outcomes


def build_daily_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_trade_outcomes(rows)
    summary["report_type"] = "daily"
    return summary

