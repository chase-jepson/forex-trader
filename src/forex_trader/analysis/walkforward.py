from __future__ import annotations

from typing import Any

from forex_trader.analysis.optimizer import optimize_opening_window
from forex_trader.backtest.runner import run_backtest
from forex_trader.backtest.split import midpoint_date, split_by_date
from forex_trader.domain.models import Candle
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy

# Out-of-sample PnL this much worse than in-sample (as a fraction) flags overfit.
_OVERFIT_DROP = 0.5


def _result_summary(result: Any) -> dict[str, Any]:
    return {
        "pnl": round(result.total_realized_pnl, 2),
        "win_rate": round(result.win_rate, 4),
        "expectancy": round(result.expectancy, 2),
        "trades": result.trades_closed,
        "max_drawdown": round(result.max_drawdown, 2),
    }


def run_walk_forward(
    *,
    candles: list[Candle],
    reward_to_risk_grid: list[float],
    max_spread_grid: list[float],
    min_trades: int = 10,
    session_start_local: str = "08:30",
    session_end_local: str = "11:30",
    session_tz: str = "America/New_York",
) -> dict[str, Any]:
    """Optimize params on the first half, validate on the held-out second half.

    Optimizing always finds *something* on the training set; only the
    out-of-sample result tells us whether the edge is real. We report both and
    flag when out-of-sample performance collapses (a curve-fit signal).
    """
    if not candles:
        return {"best_params": None, "reason": "no candles"}

    split = midpoint_date(candles)
    in_sample, out_sample = split_by_date(candles, split=split)

    opt = optimize_opening_window(
        candles=in_sample,
        reward_to_risk_grid=reward_to_risk_grid,
        max_spread_grid=max_spread_grid,
        min_trades=min_trades,
        session_start_local=session_start_local,
        session_end_local=session_end_local,
        session_tz=session_tz,
    )
    if opt.best is None:
        return {"best_params": None, "split_date": split.isoformat(), "ranked": opt.ranked}

    params = opt.best["params"]
    strategy = EurUsdOpeningWindowStrategy(
        max_spread_pips=params["max_spread_pips"],
        reward_to_risk=params["reward_to_risk"],
    )
    in_res = run_backtest(
        candles=in_sample, strategy=strategy,
        session_start_local=session_start_local,
        session_end_local=session_end_local, session_tz=session_tz,
    )
    out_res = run_backtest(
        candles=out_sample, strategy=strategy,
        session_start_local=session_start_local,
        session_end_local=session_end_local, session_tz=session_tz,
    )

    in_pnl = in_res.total_realized_pnl
    out_pnl = out_res.total_realized_pnl
    looks_overfit = in_pnl > 0 and out_pnl < in_pnl * _OVERFIT_DROP

    return {
        "best_params": params,
        "split_date": split.isoformat(),
        "in_sample": _result_summary(in_res),
        "out_of_sample": _result_summary(out_res),
        "looks_overfit": looks_overfit,
        "ranked": opt.ranked,
    }
