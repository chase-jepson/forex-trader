"""Walk-forward: optimize in-sample, validate out-of-sample, compare honestly."""
from datetime import UTC, datetime

from forex_trader.analysis.walkforward import run_walk_forward
from forex_trader.backtest.history import realistic_session_candles


def test_walk_forward_reports_in_and_out_of_sample():
    candles = realistic_session_candles(start=datetime(2026, 6, 1, tzinfo=UTC),
                                        days=20, seed=42)

    report = run_walk_forward(
        candles=candles,
        reward_to_risk_grid=[1.5, 2.0],
        max_spread_grid=[2.0],
        min_trades=3,
        session_start_local="00:00", session_end_local="23:59", session_tz="UTC",
    )

    assert report["best_params"] is not None
    assert "in_sample" in report and "out_of_sample" in report
    assert report["in_sample"]["pnl"] is not None
    assert report["out_of_sample"]["pnl"] is not None
    # The split is roughly in the middle.
    assert report["split_date"] is not None
    # Overfit flag is present (out-of-sample materially worse than in-sample).
    assert "looks_overfit" in report


def test_walk_forward_handles_no_qualifying_params():
    candles = realistic_session_candles(start=datetime(2026, 6, 1, tzinfo=UTC),
                                        days=4, seed=1)

    report = run_walk_forward(
        candles=candles,
        reward_to_risk_grid=[2.0],
        max_spread_grid=[2.0],
        min_trades=10_000,
        session_start_local="00:00", session_end_local="23:59", session_tz="UTC",
    )

    assert report["best_params"] is None
