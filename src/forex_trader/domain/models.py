from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from forex_trader.domain.enums import OrderSide, PositionStatus

PIP_SIZE = 0.0001


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    time: datetime

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> float:
        return self.ask - self.bid

    @property
    def spread_pips(self) -> float:
        return self.spread / PIP_SIZE


@dataclass(frozen=True)
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Signal:
    strategy_id: str
    symbol: str
    side: OrderSide
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: str
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def stop_loss_pips(self) -> float:
        return abs(self.entry_price - self.stop_loss) / PIP_SIZE


@dataclass(frozen=True)
class TradePlan:
    signal: Signal
    units: int
    max_hold_minutes: int
    risk_amount: float


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str

    def __iter__(self) -> Iterator[bool | str]:
        yield self.approved
        yield self.reason


@dataclass(frozen=True)
class OrderResult:
    order_id: str
    position_id: str
    accepted: bool
    reason: str
    symbol: str
    side: OrderSide
    units: int
    fill_price: float
    stop_loss: float
    take_profit: float
    opened_at: datetime


@dataclass
class Position:
    position_id: str
    symbol: str
    side: OrderSide
    units: int
    entry_price: float
    stop_loss: float
    take_profit: float
    opened_at: datetime
    status: PositionStatus = PositionStatus.OPEN
    closed_at: datetime | None = None
    close_price: float | None = None
    realized_pnl: float = 0.0

    def close(self, price: float, closed_at: datetime | None = None) -> Position:
        self.closed_at = closed_at or datetime.now(UTC)
        self.close_price = price
        self.status = PositionStatus.CLOSED
        if self.side == OrderSide.BUY:
            self.realized_pnl = (price - self.entry_price) * self.units
        else:
            self.realized_pnl = (self.entry_price - price) * self.units
        return self


@dataclass(frozen=True)
class ExecutionResult:
    cycle_id: str
    status: str
    reason: str
    signal: Signal | None = None
    order: OrderResult | None = None
