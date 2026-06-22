from __future__ import annotations

from datetime import datetime

from forex_trader.broker.base import Broker
from forex_trader.domain.models import Candle, ExecutionResult, Position, Quote, TradePlan, new_id
from forex_trader.llm.explainer import explain_decision
from forex_trader.market.sessions import must_close_position
from forex_trader.review.service import TradeReviewService
from forex_trader.risk.policy import RiskPolicy
from forex_trader.risk.sizing import calculate_units_for_risk
from forex_trader.storage.repositories import TradingRepository
from forex_trader.strategy.base import Strategy


class ExecutionOrchestrator:
    def __init__(
        self,
        *,
        strategy: Strategy,
        risk_policy: RiskPolicy,
        broker: Broker,
        repository: TradingRepository,
        equity: float,
        max_hold_minutes: int = 90,
    ) -> None:
        self.strategy = strategy
        self.risk_policy = risk_policy
        self.broker = broker
        self.repository = repository
        self.equity = equity
        self.max_hold_minutes = max_hold_minutes
        self.review_service = TradeReviewService(repository)

    def run_cycle(self, *, candles: list[Candle], quote: Quote, now: datetime) -> ExecutionResult:
        cycle_id = new_id("cycle")
        signal = self.strategy.evaluate(candles, quote)
        if signal is None:
            self.repository.save_cycle(
                cycle_id,
                now.isoformat(),
                "no_signal",
                "No documented strategy rule fired.",
                {"explanation": explain_decision(None, None)},
            )
            return ExecutionResult(cycle_id=cycle_id, status="no_signal", reason="No signal.")

        units = calculate_units_for_risk(
            equity=self.equity,
            max_risk_fraction=self.risk_policy.max_risk_per_trade,
            stop_loss_pips=signal.stop_loss_pips,
        )
        risk_amount = self.equity * self.risk_policy.max_risk_per_trade
        plan = TradePlan(
            signal=signal,
            units=units,
            max_hold_minutes=self.max_hold_minutes,
            risk_amount=risk_amount,
        )
        decision = self.risk_policy.validate_trade(
            equity=self.equity,
            open_positions=len(self.broker.list_open_positions()),
            stop_loss_pips=signal.stop_loss_pips,
            take_profit=signal.take_profit,
            risk_amount=plan.risk_amount,
            max_hold_minutes=plan.max_hold_minutes,
        )
        explanation = explain_decision(signal, decision)
        if not decision.approved:
            self.repository.save_cycle(
                cycle_id,
                now.isoformat(),
                "blocked",
                decision.reason,
                {"signal": signal.__dict__, "explanation": explanation},
            )
            self.review_service.create_review(
                trade_id=cycle_id,
                outcome="blocked",
                pnl=0.0,
                market_context={"spread_pips": quote.spread_pips},
                rule_snapshot={"strategy": signal.strategy_id, "reason": signal.reason},
                risk_reason=decision.reason,
                mistake_tags=["rule_blocked"],
            )
            return ExecutionResult(
                cycle_id=cycle_id,
                status="blocked",
                reason=decision.reason,
                signal=signal,
            )

        order = self.broker.place_market_order(
            symbol=signal.symbol,
            side=signal.side,
            units=plan.units,
            price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            opened_at=now,
        )
        self.repository.save_cycle(
            cycle_id,
            now.isoformat(),
            "ordered",
            order.reason,
            {"signal": signal.__dict__, "order": order.__dict__, "explanation": explanation},
        )
        return ExecutionResult(
            cycle_id=cycle_id,
            status="ordered",
            reason=order.reason,
            signal=signal,
            order=order,
        )

    def close_expired_positions(
        self,
        *,
        now: datetime,
        price: float,
        session_end_local: str,
    ) -> list[Position]:
        closed: list[Position] = []
        for position in self.broker.list_open_positions():
            if must_close_position(
                position.opened_at,
                now,
                self.max_hold_minutes,
                session_end_local,
            ):
                closed_position = self.broker.close_position(position.position_id, price, now)
                closed.append(closed_position)
                self.review_service.create_review(
                    trade_id=position.position_id,
                    outcome="win" if closed_position.realized_pnl > 0 else "loss",
                    pnl=closed_position.realized_pnl,
                    market_context={"exit_price": price},
                    rule_snapshot={"exit": "max_hold_or_session_cutoff"},
                    risk_reason="Forced close policy applied.",
                    mistake_tags=["time_exit"],
                )
        return closed
