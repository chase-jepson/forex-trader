from __future__ import annotations

from forex_trader.backtest.runner import BacktestResult, run_backtest
from forex_trader.domain.models import Candle
from forex_trader.market.sessions import DEFAULT_SESSION_TZ
from forex_trader.strategy.base import Strategy


def compare_strategies(
    *,
    candles: list[Candle],
    strategies: dict[str, Strategy],
    starting_equity: float = 10_000.0,
    session_start_local: str = "05:00",
    session_end_local: str = "09:00",
    session_tz: str = DEFAULT_SESSION_TZ,
) -> dict[str, BacktestResult]:
    """Backtest each named strategy over the same candles and return results.

    Every strategy runs through the identical risk engine, broker, and session
    settings, so their metrics are directly comparable.
    """
    return {
        name: run_backtest(
            candles=candles,
            strategy=strategy,
            starting_equity=starting_equity,
            session_start_local=session_start_local,
            session_end_local=session_end_local,
            session_tz=session_tz,
        )
        for name, strategy in strategies.items()
    }


def format_comparison(table: dict[str, BacktestResult]) -> str:
    """Render a comparison table as plain text for reports and the CLI."""
    header = (
        f"{'strategy':<20} {'closed':>7} {'win%':>7} "
        f"{'expectancy':>11} {'pnl':>10} {'max_dd':>10}"
    )
    lines = [header, "-" * len(header)]
    for name, r in table.items():
        lines.append(
            f"{name:<20} {r.trades_closed:>7} {r.win_rate * 100:>6.1f}% "
            f"{r.expectancy:>11.2f} {r.total_realized_pnl:>10.2f} {r.max_drawdown:>10.2f}"
        )
    return "\n".join(lines)
