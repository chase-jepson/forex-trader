from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.domain.models import PIP_SIZE, Candle, Quote
from forex_trader.execution.orchestrator import ExecutionOrchestrator
from forex_trader.market.sessions import DEFAULT_SESSION_TZ
from forex_trader.risk.policy import RiskPolicy
from forex_trader.storage.repositories import TradingRepository
from forex_trader.strategy.base import Strategy
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


@dataclass(frozen=True)
class BacktestResult:
    starting_equity: float
    final_equity: float
    total_realized_pnl: float
    trades_closed: int
    trades_blocked: int
    wins: int
    losses: int
    win_rate: float
    expectancy: float
    max_drawdown: float
    equity_curve: list[float] = field(default_factory=list)


def _max_drawdown(curve: list[float]) -> float:
    """Largest peak-to-trough drop in account currency over the curve."""
    peak = curve[0] if curve else 0.0
    worst = 0.0
    for value in curve:
        peak = max(peak, value)
        worst = max(worst, peak - value)
    return worst


def run_backtest(
    *,
    candles: list[Candle],
    strategy: Strategy | None = None,
    starting_equity: float = 10_000.0,
    window_size: int = 6,
    max_risk_per_trade: float = 0.0025,
    max_daily_loss: float = 0.01,
    max_open_positions: int = 1,
    max_hold_minutes: int = 90,
    half_spread_pips: float = 1.0,
    session_start_local: str = "05:00",
    session_end_local: str = "09:00",
    session_tz: str = DEFAULT_SESSION_TZ,
) -> BacktestResult:
    """Step a strategy through historical candles via the live orchestrator.

    Uses the same risk engine, broker fill model, and review flow as live
    execution so backtest evidence is comparable to simulated/practice runs.
    """
    broker = SimulatedBroker(half_spread_pips=half_spread_pips)
    policy = RiskPolicy(
        max_risk_per_trade=max_risk_per_trade,
        max_daily_loss=max_daily_loss,
        max_open_positions=max_open_positions,
    )
    active_strategy = strategy or EurUsdOpeningWindowStrategy()

    # Backtests persist to a throwaway database so the audit trail mechanics are
    # exercised without polluting the operational store.
    with tempfile.TemporaryDirectory() as tmp:
        repository = TradingRepository(Path(tmp) / "backtest.db")
        orchestrator = ExecutionOrchestrator(
            strategy=active_strategy,
            risk_policy=policy,
            broker=broker,
            repository=repository,
            equity=starting_equity,
            max_hold_minutes=max_hold_minutes,
            session_start_local=session_start_local,
            session_end_local=session_end_local,
            session_tz=session_tz,
        )

        equity_curve = [starting_equity]
        half_spread = half_spread_pips * PIP_SIZE
        prev_date = candles[0].time.date() if candles else None

        for index in range(1, len(candles)):
            window = candles[max(0, index - window_size) : index + 1]
            current = candles[index]

            # The daily-loss cap is per day; reset the daily bucket at each
            # calendar-day boundary so one bad day cannot block later days.
            if current.time.date() != prev_date:
                orchestrator.reset_daily_pnl()
                prev_date = current.time.date()
            quote = Quote(
                symbol="EUR_USD",
                bid=current.close - half_spread,
                ask=current.close + half_spread,
                time=current.time,
            )
            broker.set_quote(quote)

            # Resolve intra-bar stop/target fills first, then time/session exits.
            orchestrator.resolve_stop_target_fills(candle=current, now=current.time)
            orchestrator.close_expired_positions(
                now=current.time,
                price=None,
                session_end_local=session_end_local,
            )
            orchestrator.run_cycle(candles=window, quote=quote, now=current.time)
            # Equity tracks cumulative PnL across the whole run, not the daily
            # bucket (which resets at day boundaries).
            equity_curve.append(starting_equity + orchestrator.cumulative_realized_pnl)

        reviews = repository.list_reviews()

    closed = [r for r in reviews if r["outcome"] in {"win", "loss", "scratch"}]
    blocked = [r for r in reviews if r["outcome"] == "blocked"]
    wins = sum(1 for r in closed if r["outcome"] == "win")
    losses = sum(1 for r in closed if r["outcome"] == "loss")
    total_pnl = sum(float(r.get("pnl", 0.0)) for r in closed)
    decided = wins + losses
    win_rate = 0.0 if decided == 0 else wins / decided
    expectancy = 0.0 if not closed else total_pnl / len(closed)

    return BacktestResult(
        starting_equity=starting_equity,
        final_equity=starting_equity + total_pnl,
        total_realized_pnl=total_pnl,
        trades_closed=len(closed),
        trades_blocked=len(blocked),
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        expectancy=expectancy,
        max_drawdown=_max_drawdown(equity_curve),
        equity_curve=equity_curve,
    )
