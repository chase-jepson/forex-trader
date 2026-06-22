from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from forex_trader.domain.enums import ReviewStatus


@dataclass(frozen=True)
class TradeReview:
    review_id: str
    trade_id: str
    outcome: str
    pnl: float
    market_context: dict[str, Any]
    rule_snapshot: dict[str, Any]
    risk_reason: str
    mistake_tags: list[str]
    improvement_hypothesis: str
    status: ReviewStatus = ReviewStatus.NEW
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

