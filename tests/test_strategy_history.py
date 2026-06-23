"""Strategies declare how much candle history they need; the runner honors it."""
from datetime import UTC, datetime

from forex_trader.backtest.history import realistic_session_candles
from forex_trader.backtest.runner import run_backtest
from forex_trader.strategy.eurusd_mean_reversion import EurUsdMeanReversionStrategy
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


def test_strategies_declare_required_history():
    assert EurUsdOpeningWindowStrategy().required_history >= 2
    mr = EurUsdMeanReversionStrategy(lookback=10)
    assert mr.required_history > 10  # needs lookback+1 closes


def test_mean_reversion_trades_when_window_covers_its_lookback():
    candles = realistic_session_candles(start=datetime(2026, 6, 1, tzinfo=UTC),
                                        days=10, seed=42)

    result = run_backtest(
        candles=candles,
        strategy=EurUsdMeanReversionStrategy(lookback=10, deviation_pips=5.0),
        session_start_local="00:00", session_end_local="23:59", session_tz="UTC",
    )

    # With the window auto-sized to the strategy's history, it now trades.
    assert result.trades_closed > 0
