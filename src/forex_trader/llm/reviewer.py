from __future__ import annotations

from forex_trader.review.models import TradeReview


def summarize_review(review: TradeReview) -> str:
    tags = ", ".join(review.mistake_tags) if review.mistake_tags else "none"
    return (
        f"Trade {review.trade_id} ended as {review.outcome} with PnL {review.pnl:.2f}. "
        f"Risk note: {review.risk_reason or 'not recorded'}. Tags: {tags}. "
        f"Next hypothesis: {review.improvement_hypothesis}"
    )

