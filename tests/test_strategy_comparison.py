"""Compare multiple strategies over the same candle series."""
from datetime import UTC, datetime

from forex_trader.backtest.compare import compare_strategies
from forex_trader.backtest.feed import generate_synthetic_candles
from forex_trader.strategy.eurusd_mean_reversion import EurUsdMeanReversionStrategy
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


def test_compare_runs_each_strategy_over_same_candles():
    candles = generate_synthetic_candles(
        start=datetime(2026, 6, 22, 5, 0, tzinfo=UTC), count=300, seed=3,
    )
    strategies = {
        "opening_window": EurUsdOpeningWindowStrategy(),
        "mean_reversion": EurUsdMeanReversionStrategy(lookback=10),
    }

    table = compare_strategies(
        candles=candles, strategies=strategies,
        session_start_local="00:00", session_end_local="23:59", session_tz="UTC",
    )

    assert set(table.keys()) == {"opening_window", "mean_reversion"}
    for result in table.values():
        assert result.starting_equity == 10_000.0
        assert hasattr(result, "expectancy")


def test_compare_is_deterministic():
    candles = generate_synthetic_candles(
        start=datetime(2026, 6, 22, 5, 0, tzinfo=UTC), count=200, seed=5,
    )
    strategies = {"mean_reversion": EurUsdMeanReversionStrategy(lookback=10)}
    kw = dict(session_start_local="00:00", session_end_local="23:59", session_tz="UTC")

    a = compare_strategies(candles=candles, strategies=strategies, **kw)
    b = compare_strategies(candles=candles, strategies=strategies, **kw)

    assert a["mean_reversion"].final_equity == b["mean_reversion"].final_equity
