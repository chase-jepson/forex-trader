from __future__ import annotations

from dataclasses import replace
from typing import Any

from forex_trader.domain.models import new_id
from forex_trader.llm.reviewer import summarize_review
from forex_trader.review.models import TradeReview
from forex_trader.storage.repositories import TradingRepository


class TradeReviewService:
    def __init__(self, repository: TradingRepository | None = None) -> None:
        self.repository = repository

    def create_review(
        self,
        *,
        trade_id: str,
        outcome: str,
        pnl: float,
        market_context: dict[str, Any] | None = None,
        rule_snapshot: dict[str, Any] | None = None,
        risk_reason: str = "",
        mistake_tags: list[str] | None = None,
    ) -> TradeReview:
        tags = mistake_tags or []
        improvement = self._suggest_improvement(outcome, tags)
        review = TradeReview(
            review_id=new_id("rev"),
            trade_id=trade_id,
            outcome=outcome,
            pnl=pnl,
            market_context=market_context or {},
            rule_snapshot=rule_snapshot or {},
            risk_reason=risk_reason,
            mistake_tags=tags,
            improvement_hypothesis=improvement,
        )
        review = replace(review, summary=summarize_review(review))
        if self.repository is not None:
            self.repository.save_review(
                review_id=review.review_id,
                trade_id=review.trade_id,
                outcome=review.outcome,
                payload=review.__dict__,
            )
        return review

    def _suggest_improvement(self, outcome: str, mistake_tags: list[str]) -> str:
        if outcome == "blocked":
            return "Review whether the blocking rule protected the account or is too restrictive."
        if "stop_too_tight" in mistake_tags:
            return "Test whether the stop distance is too tight for the setup volatility."
        if outcome == "loss":
            return "Compare the entry context with similar winning and losing setups."
        return "Keep collecting examples before changing rules."

