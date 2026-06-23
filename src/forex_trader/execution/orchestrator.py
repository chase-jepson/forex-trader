from __future__ import annotations

from datetime import datetime

from forex_trader.broker.base import Broker
from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, ExecutionResult, Position, Quote, TradePlan, new_id
from forex_trader.llm.explainer import explain_decision
from forex_trader.market.sessions import (
    DEFAULT_SESSION_TZ,
    can_open_new_trade,
    must_close_position,
)
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
        session_start_local: str = "05:00",
        session_end_local: str = "09:00",
        session_tz: str = DEFAULT_SESSION_TZ,
    ) -> None:
        self.strategy = strategy
        self.risk_policy = risk_policy
        self.broker = broker
        self.repository = repository
        self.equity = equity
        self.max_hold_minutes = max_hold_minutes
        self.session_start_local = session_start_local
        self.session_end_local = session_end_local
        self.session_tz = session_tz
        self.review_service = TradeReviewService(repository)
        # Realized PnL for the current trading day; feeds the daily-loss cap and
        # is reset at each day boundary via reset_daily_pnl().
        self.daily_realized_pnl = 0.0
        # Realized PnL across the whole run; never reset, feeds the equity curve.
        self.cumulative_realized_pnl = 0.0

    def reset_daily_pnl(self) -> None:
        """Clear the daily PnL bucket at a trading-day boundary.

        The daily-loss cap is a *per-day* limit, so a loss on one day must not
        carry forward and permanently block trading on later days.
        """
        self.daily_realized_pnl = 0.0

    def _record_realized_pnl(self, pnl: float) -> None:
        self.daily_realized_pnl += pnl
        self.cumulative_realized_pnl += pnl

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

        if not can_open_new_trade(
            now,
            self.session_start_local,
            self.session_end_local,
            self.session_tz,
        ):
            reason = "Outside the trading session window."
            self.repository.save_cycle(
                cycle_id,
                now.isoformat(),
                "blocked",
                reason,
                {"signal": signal.__dict__, "explanation": reason},
            )
            self.review_service.create_review(
                trade_id=cycle_id,
                outcome="blocked",
                pnl=0.0,
                market_context={"spread_pips": quote.spread_pips},
                rule_snapshot={"strategy": signal.strategy_id, "reason": signal.reason},
                risk_reason=reason,
                mistake_tags=["outside_session"],
            )
            return ExecutionResult(
                cycle_id=cycle_id, status="blocked", reason=reason, signal=signal
            )

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
            daily_realized_pnl=self.daily_realized_pnl,
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
        self.repository.open_trade_story(
            position_id=order.position_id,
            opened_at=now.isoformat(),
            side=str(signal.side),
            entry_price=order.fill_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            units=order.units,
            signal_reason=signal.reason,
            signal_metadata=dict(signal.metadata),
            risk_reason=decision.reason,
            context_candles=[_candle_to_dict(candle) for candle in candles],
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
        price: float | None,
        session_end_local: str,
    ) -> list[Position]:
        closed: list[Position] = []
        for position in self.broker.list_open_positions():
            if must_close_position(
                position.opened_at,
                now,
                self.max_hold_minutes,
                session_end_local,
                self.session_tz,
            ):
                closed_position = self.broker.close_position(position.position_id, price, now)
                closed.append(closed_position)
                self._record_realized_pnl(closed_position.realized_pnl)
                self.review_service.create_review(
                    trade_id=position.position_id,
                    outcome=_outcome_for_pnl(closed_position.realized_pnl),
                    pnl=closed_position.realized_pnl,
                    market_context={"exit_price": closed_position.close_price},
                    rule_snapshot={"exit": "max_hold_or_session_cutoff"},
                    risk_reason="Forced close policy applied.",
                    mistake_tags=["time_exit"],
                )
                self._close_story(closed_position, now, "max_hold_or_session_cutoff")
        return closed

    def resolve_stop_target_fills(
        self,
        *,
        candle: Candle,
        now: datetime,
    ) -> list[Position]:
        """Close open positions whose stop or target was touched intra-bar.

        When a single candle spans both the stop and the target we resolve the
        stop first (pessimistic convention), since we cannot see intra-bar
        ordering. Fills occur at the exact stop/target price.
        """
        closed: list[Position] = []
        for position in self.broker.list_open_positions():
            hit_price = self._stop_or_target_hit(position, candle)
            if hit_price is None:
                continue
            closed_position = self._close_at(position.position_id, hit_price, now)
            closed.append(closed_position)
            self._record_realized_pnl(closed_position.realized_pnl)
            exit_kind = "stop_loss" if hit_price == position.stop_loss else "take_profit"
            self.review_service.create_review(
                trade_id=position.position_id,
                outcome=_outcome_for_pnl(closed_position.realized_pnl),
                pnl=closed_position.realized_pnl,
                market_context={"exit_price": hit_price, "candle_high": candle.high,
                                "candle_low": candle.low},
                rule_snapshot={"exit": exit_kind},
                risk_reason=f"Intra-bar {exit_kind} fill.",
                mistake_tags=["rule_failed" if exit_kind == "stop_loss" else "rule_worked"],
            )
            self._close_story(closed_position, now, exit_kind)
        return closed

    @staticmethod
    def _stop_or_target_hit(position: Position, candle: Candle) -> float | None:
        if position.side == OrderSide.BUY:
            stop_hit = candle.low <= position.stop_loss
            target_hit = candle.high >= position.take_profit
        else:
            stop_hit = candle.high >= position.stop_loss
            target_hit = candle.low <= position.take_profit
        if stop_hit:
            return position.stop_loss  # pessimistic: stop resolves first
        if target_hit:
            return position.take_profit
        return None

    def _close_at(self, position_id: str, price: float, now: datetime) -> Position:
        close_at = getattr(self.broker, "close_position_at", None)
        if callable(close_at):
            return close_at(position_id, price, now)  # type: ignore[no-any-return]
        return self.broker.close_position(position_id, price, now)

    def _close_story(self, position: Position, now: datetime, exit_reason: str) -> None:
        """Update the persisted trade story when a position closes."""
        self.repository.close_trade_story(
            position_id=position.position_id,
            closed_at=now.isoformat(),
            close_price=position.close_price if position.close_price is not None else 0.0,
            outcome=_outcome_for_pnl(position.realized_pnl),
            pnl=position.realized_pnl,
            exit_reason=exit_reason,
        )


def _candle_to_dict(candle: Candle) -> dict[str, object]:
    return {
        "time": candle.time.isoformat(),
        "open": candle.open,
        "high": candle.high,
        "low": candle.low,
        "close": candle.close,
    }


def _outcome_for_pnl(pnl: float) -> str:
    if pnl > 0:
        return "win"
    if pnl < 0:
        return "loss"
    return "scratch"
