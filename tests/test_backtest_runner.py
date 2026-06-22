"""Backtest runner steps an orchestrator over historical candles."""
from datetime import UTC, datetime

from forex_trader.backtest.feed import generate_synthetic_candles
from forex_trader.backtest.runner import BacktestResult, run_backtest


def test_backtest_produces_equity_curve_and_metrics():
    candles = generate_synthetic_candles(
        start=datetime(2026, 6, 22, 5, 0, tzinfo=UTC), count=200, seed=42,
    )

    result = run_backtest(
        candles=candles,
        starting_equity=10_000.0,
        # Wide-open window/tz so the synthetic series can trade.
        session_start_local="00:00",
        session_end_local="23:59",
        session_tz="UTC",
    )

    assert isinstance(result, BacktestResult)
    assert len(result.equity_curve) >= 1
    assert result.starting_equity == 10_000.0
    # Final equity equals starting plus the sum of realized PnL.
    assert round(result.final_equity, 6) == round(
        10_000.0 + result.total_realized_pnl, 6
    )
    assert result.max_drawdown >= 0.0
    assert 0.0 <= result.win_rate <= 1.0


def test_backtest_with_no_trades_is_flat():
    # A tiny series that never breaks out -> no trades, flat equity.
    candles = generate_synthetic_candles(
        start=datetime(2026, 6, 22, 5, 0, tzinfo=UTC), count=3, seed=1,
    )

    result = run_backtest(
        candles=candles,
        starting_equity=5_000.0,
        session_start_local="00:00",
        session_end_local="23:59",
        session_tz="UTC",
    )

    assert result.final_equity == 5_000.0
    assert result.trades_closed == 0


def test_backtest_is_deterministic():
    candles = generate_synthetic_candles(
        start=datetime(2026, 6, 22, 5, 0, tzinfo=UTC), count=150, seed=9,
    )
    kwargs = dict(
        starting_equity=10_000.0,
        session_start_local="00:00",
        session_end_local="23:59",
        session_tz="UTC",
    )

    a = run_backtest(candles=candles, **kwargs)
    b = run_backtest(candles=candles, **kwargs)

    assert a.final_equity == b.final_equity
    assert a.trades_closed == b.trades_closed
