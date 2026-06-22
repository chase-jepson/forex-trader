from __future__ import annotations

from datetime import datetime

from forex_trader.backtest.compare import compare_strategies, format_comparison
from forex_trader.backtest.history import realistic_session_candles
from forex_trader.backtest.runner import BacktestResult
from forex_trader.strategy.base import Strategy
from forex_trader.strategy.eurusd_mean_reversion import EurUsdMeanReversionStrategy
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy
from forex_trader.strategy.news_avoidance import NewsAvoidanceStrategy

MIN_TRADES_FOR_VERDICT = 20


def _evidence_strategies() -> dict[str, Strategy]:
    """All candidate strategies, including news-avoidance wrapping the breakout."""
    return {
        "opening_window": EurUsdOpeningWindowStrategy(),
        "mean_reversion": EurUsdMeanReversionStrategy(lookback=15),
        "news_avoidance": NewsAvoidanceStrategy(
            inner=EurUsdOpeningWindowStrategy(), events=[]
        ),
    }


def verdict_for(result: BacktestResult) -> str:
    """A plain-English verdict from a backtest result.

    This is a screening heuristic over a fixture, NOT a claim of real edge — it
    flags which strategies are worth investigating with real data.
    """
    if result.trades_closed < MIN_TRADES_FOR_VERDICT:
        return (
            f"insufficient evidence ({result.trades_closed} trades; "
            f"need {MIN_TRADES_FOR_VERDICT}+)"
        )
    if result.expectancy > 0 and result.total_realized_pnl > 0:
        return "positive expectancy on this fixture — investigate with real data"
    return "no edge on this fixture"


def build_evidence_report(*, days: int, seed: int) -> tuple[dict[str, BacktestResult], str]:
    """Run all strategies over the realistic fixture and render a report."""
    start = datetime.fromisoformat("2026-06-01T00:00:00+00:00")
    candles = realistic_session_candles(start=start, days=days, seed=seed)
    table = compare_strategies(
        candles=candles,
        strategies=_evidence_strategies(),
        session_start_local="00:00",
        session_end_local="23:59",
        session_tz="UTC",
    )

    lines = [
        "# Strategy Evidence Report",
        "",
        f"Source: realistic offline fixture ({days} days, seed {seed}). "
        "This is NOT real market data — it screens strategies before testing on real history.",
        "",
        "```",
        format_comparison(table),
        "```",
        "",
        "## Verdicts",
        "",
    ]
    for name, result in table.items():
        lines.append(f"- **{name}**: {verdict_for(result)}")
    lines.append("")
    return table, "\n".join(lines)
