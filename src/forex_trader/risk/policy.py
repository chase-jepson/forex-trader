from __future__ import annotations

from dataclasses import dataclass

from forex_trader.domain.models import RiskDecision


@dataclass(frozen=True)
class RiskPolicy:
    max_risk_per_trade: float
    max_daily_loss: float
    max_open_positions: int

    def validate_trade(
        self,
        *,
        equity: float,
        open_positions: int,
        stop_loss_pips: float | None,
        take_profit: float | None,
        risk_amount: float,
        max_hold_minutes: int | None,
        daily_realized_pnl: float = 0.0,
    ) -> RiskDecision:
        if open_positions >= self.max_open_positions:
            return RiskDecision(False, "Max open position limit reached.")
        if stop_loss_pips is None or stop_loss_pips <= 0:
            return RiskDecision(False, "Stop loss is required.")
        if take_profit is None:
            return RiskDecision(False, "Take profit or explicit target is required.")
        if max_hold_minutes is None or max_hold_minutes <= 0:
            return RiskDecision(False, "Max hold time is required.")
        max_risk_amount = equity * self.max_risk_per_trade
        if risk_amount > max_risk_amount:
            percent = self.max_risk_per_trade * 100
            return RiskDecision(False, f"Risk exceeds {percent:.2f}% per-trade limit.")
        # A cap of 0 (or less) disables the daily-loss limit entirely — useful
        # while learning on a demo account. Any positive value is enforced.
        if self.max_daily_loss > 0 and daily_realized_pnl < 0:
            if abs(daily_realized_pnl) >= equity * self.max_daily_loss:
                return RiskDecision(False, "Daily loss limit reached.")
        return RiskDecision(True, "Approved: trade is within risk policy.")

