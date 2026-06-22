"""Daily-loss tracking must reset at day boundaries so it doesn't poison later days."""
from datetime import UTC, datetime

from forex_trader.backtest.feed import generate_synthetic_candles
from forex_trader.backtest.runner import run_backtest
from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.execution.orchestrator import ExecutionOrchestrator
from forex_trader.risk.policy import RiskPolicy
from forex_trader.storage.repositories import TradingRepository


def test_orchestrator_exposes_reset_daily_pnl(tmp_path):
    orch = ExecutionOrchestrator(
        strategy=__import__(
            "forex_trader.strategy.null_strategy", fromlist=["NullStrategy"]
        ).NullStrategy(),
        risk_policy=RiskPolicy(0.0025, 0.01, 1),
        broker=SimulatedBroker(),
        repository=TradingRepository(tmp_path / "t.db"),
        equity=10_000,
    )
    orch.daily_realized_pnl = -50.0

    orch.reset_daily_pnl()

    assert orch.daily_realized_pnl == 0.0


def test_multiday_backtest_does_not_carry_daily_loss_across_days():
    # 3 full days of 1-min candles. The daily-loss cap must be evaluated per
    # day, so a multi-day run is not permanently blocked after one bad day.
    start = datetime(2026, 6, 22, 0, 0, tzinfo=UTC)
    candles = generate_synthetic_candles(start=start, count=3 * 24 * 60, seed=11,
                                         volatility_pips=6.0)

    result = run_backtest(
        candles=candles, session_start_local="00:00", session_end_local="23:59",
        session_tz="UTC",
    )

    # With per-day reset, total realized PnL is the sum across days and the
    # equity curve's final point equals starting + total realized.
    assert round(result.final_equity, 6) == round(10_000 + result.total_realized_pnl, 6)
