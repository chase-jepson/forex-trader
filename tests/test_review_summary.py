"""Each created review should carry a human-readable summary line."""
from forex_trader.review.service import TradeReviewService


def test_review_includes_human_summary():
    service = TradeReviewService()

    review = service.create_review(
        trade_id="t-1",
        outcome="loss",
        pnl=-42.0,
        mistake_tags=["stop_too_tight"],
    )

    assert "t-1" in review.summary
    assert "loss" in review.summary.lower()
