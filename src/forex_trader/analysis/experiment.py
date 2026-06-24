from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from forex_trader.backtest.runner import run_backtest
from forex_trader.backtest.split import midpoint_date, split_by_date
from forex_trader.domain.models import Candle
from forex_trader.strategy.base import Strategy

# A strategy needs at least this many out-of-sample trades for the result to be
# statistically meaningful rather than luck.
MIN_MEANINGFUL_TRADES = 15


def load_cached_candles(path: str | Path) -> list[Candle]:
    rows = json.loads(Path(path).read_text())
    return [
        Candle(
            time=datetime.fromisoformat(r["time"]),
            open=r["open"], high=r["high"], low=r["low"], close=r["close"],
        )
        for r in rows
    ]


def risk_adjusted_score(*, pnl: float, max_drawdown: float, trades: int) -> float:
    """Score = profit per unit of drawdown, discounted when trades are sparse.

    Maximizes profit while minimizing risk (drawdown), and refuses to reward a
    result built on too few trades. A losing strategy always scores <= 0.
    """
    if pnl <= 0:
        return pnl  # negative or zero PnL is never attractive
    denom = max(max_drawdown, 1.0)
    base = pnl / denom
    # Smoothly discount until trades reach the meaningful threshold.
    confidence = min(1.0, trades / MIN_MEANINGFUL_TRADES)
    return base * confidence


def _summary(result: Any) -> dict[str, Any]:
    return {
        "pnl": round(result.total_realized_pnl, 2),
        "win_rate": round(result.win_rate, 4),
        "expectancy": round(result.expectancy, 2),
        "trades": result.trades_closed,
        "max_drawdown": round(result.max_drawdown, 2),
        "score": round(
            risk_adjusted_score(
                pnl=result.total_realized_pnl,
                max_drawdown=result.max_drawdown,
                trades=result.trades_closed,
            ),
            4,
        ),
    }


def walk_forward_strategy(
    strategy: Strategy,
    *,
    candles: list[Candle],
    session_start_local: str = "08:30",
    session_end_local: str = "11:30",
    session_tz: str = "America/New_York",
) -> dict[str, Any]:
    """Backtest a strategy on the in-sample half and the held-out out-of-sample
    half, returning risk-adjusted summaries for each."""
    split = midpoint_date(candles)
    in_sample, out_sample = split_by_date(candles, split=split)
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
    return {
        "split_date": split.isoformat(),
        "in_sample": _summary(in_res),
        "out_of_sample": _summary(out_res),
    }
