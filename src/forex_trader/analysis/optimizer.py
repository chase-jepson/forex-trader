from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from forex_trader.backtest.runner import run_backtest
from forex_trader.domain.models import Candle
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


@dataclass(frozen=True)
class OptimizationResult:
    best: dict[str, Any] | None
    ranked: list[dict[str, Any]] = field(default_factory=list)


def optimize_opening_window(
    *,
    candles: list[Candle],
    reward_to_risk_grid: list[float],
    max_spread_grid: list[float],
    min_trades: int = 10,
    session_start_local: str = "08:30",
    session_end_local: str = "11:30",
    session_tz: str = "America/New_York",
    starting_equity: float = 10_000.0,
) -> OptimizationResult:
    """Grid-search opening-window params on in-sample candles, ranked by PnL.

    Only candidates that took at least `min_trades` trades are ranked, so a
    single lucky trade cannot win. The result is the parameter set with the
    highest realized PnL on this data — to be VALIDATED out-of-sample before
    being trusted (optimizing always finds something on the training set).
    """
    candidates: list[dict[str, Any]] = []
    for rr in reward_to_risk_grid:
        for spread in max_spread_grid:
            strategy = EurUsdOpeningWindowStrategy(
                max_spread_pips=spread, reward_to_risk=rr
            )
            result = run_backtest(
                candles=candles,
                strategy=strategy,
                starting_equity=starting_equity,
                session_start_local=session_start_local,
                session_end_local=session_end_local,
                session_tz=session_tz,
            )
            if result.trades_closed < min_trades:
                continue
            candidates.append(
                {
                    "params": {"reward_to_risk": rr, "max_spread_pips": spread},
                    "pnl": round(result.total_realized_pnl, 2),
                    "win_rate": round(result.win_rate, 4),
                    "expectancy": round(result.expectancy, 2),
                    "trades": result.trades_closed,
                    "max_drawdown": round(result.max_drawdown, 2),
                }
            )

    ranked = sorted(candidates, key=lambda c: c["pnl"], reverse=True)
    return OptimizationResult(best=ranked[0] if ranked else None, ranked=ranked)
