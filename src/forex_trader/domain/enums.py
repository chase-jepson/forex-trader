from __future__ import annotations

from enum import StrEnum


class AppMode(StrEnum):
    SIMULATED = "simulated"
    PRACTICE = "practice"
    LIVE = "live"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class PositionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class TradeOutcome(StrEnum):
    WIN = "win"
    LOSS = "loss"
    SCRATCH = "scratch"
    BLOCKED = "blocked"
    OPEN = "open"


class ReviewStatus(StrEnum):
    NEW = "new"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class ResearchStatus(StrEnum):
    DRAFT = "draft"
    READY_FOR_SIM = "ready_for_sim"
    REJECTED = "rejected"

