from datetime import UTC, datetime

import pytest

from forex_trader.broker.oanda import OandaBroker
from forex_trader.config import Settings
from forex_trader.main import validate_startup
from forex_trader.reporting.metrics import summarize_trade_outcomes
from forex_trader.review.service import TradeReviewService


def test_losing_trade_generates_review_record_with_improvement_hypothesis():
    service = TradeReviewService()

    review = service.create_review(
        trade_id="t-123",
        outcome="loss",
        pnl=-42.0,
        market_context={"spread_pips": 1.2},
        rule_snapshot={"strategy": "eurusd_opening_window"},
        risk_reason="Approved: within 0.25% risk.",
        mistake_tags=["stop_too_tight"],
    )

    assert review.trade_id == "t-123"
    assert review.outcome == "loss"
    assert review.improvement_hypothesis


def test_reporting_metrics_include_win_rate_and_blocked_reasons():
    summary = summarize_trade_outcomes(
        [
            {"outcome": "win", "pnl": 20, "hold_minutes": 30},
            {"outcome": "loss", "pnl": -10, "hold_minutes": 20},
            {"outcome": "blocked", "reason": "Max open positions reached"},
        ]
    )

    assert summary["win_rate"] == 0.5
    assert summary["realized_pnl"] == 10
    assert summary["top_blocked_reasons"] == [("Max open positions reached", 1)]


def test_oanda_practice_mode_requires_credentials():
    with pytest.raises(ValueError, match="OANDA credentials"):
        OandaBroker(mode="practice", account_id="", token="")


def test_live_mode_requires_explicit_enable_and_completed_gates(tmp_path):
    settings = Settings(
        app_mode="live",
        enable_live_trading=False,
        emergency_stop_path=str(tmp_path / "STOP"),
    )

    status = validate_startup(settings, simulation_complete=True, practice_complete=True)

    assert status.ok is False
    assert "explicitly enabled" in status.reason


def test_dashboard_module_imports_without_streamlit_runtime():
    from forex_trader.dashboard.app import build_dashboard_snapshot

    snapshot = build_dashboard_snapshot(
        quote={
            "symbol": "EUR_USD",
            "bid": 1.1,
            "ask": 1.1002,
            "time": datetime.now(UTC).isoformat(),
        },
        cycles=[],
        reviews=[],
    )

    assert snapshot["live_market"]["symbol"] == "EUR_USD"
