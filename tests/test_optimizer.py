"""Grid-search optimizer over strategy params on in-sample candles."""
from datetime import UTC, datetime

from forex_trader.analysis.optimizer import OptimizationResult, optimize_opening_window
from forex_trader.backtest.history import realistic_session_candles


def test_optimizer_returns_best_params_by_pnl():
    candles = realistic_session_candles(start=datetime(2026, 6, 1, tzinfo=UTC),
                                        days=10, seed=42)

    result = optimize_opening_window(
        candles=candles,
        reward_to_risk_grid=[1.5, 2.0, 3.0],
        max_spread_grid=[1.5, 2.5],
        min_trades=5,
        session_start_local="00:00", session_end_local="23:59", session_tz="UTC",
    )

    assert isinstance(result, OptimizationResult)
    assert result.best is not None
    assert "reward_to_risk" in result.best["params"]
    # Every candidate with enough trades is ranked; best has the top PnL.
    pnls = [c["pnl"] for c in result.ranked]
    assert pnls == sorted(pnls, reverse=True)


def test_optimizer_respects_min_trades_floor():
    candles = realistic_session_candles(start=datetime(2026, 6, 1, tzinfo=UTC),
                                        days=3, seed=1)

    result = optimize_opening_window(
        candles=candles,
        reward_to_risk_grid=[2.0],
        max_spread_grid=[2.0],
        min_trades=10_000,  # impossibly high -> nothing qualifies
        session_start_local="00:00", session_end_local="23:59", session_tz="UTC",
    )

    assert result.best is None  # no candidate met the trade floor
