"""Routine 'max open position' blocks should not flood the review log."""
from datetime import UTC, datetime

from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.domain.models import Candle, Quote
from forex_trader.execution.orchestrator import ExecutionOrchestrator
from forex_trader.risk.policy import RiskPolicy
from forex_trader.storage.repositories import TradingRepository
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


def _inputs(now):
    candles = [
        Candle(time=now, open=1.1000, high=1.1010, low=1.0990, close=1.1005),
        Candle(time=now, open=1.1005, high=1.1020, low=1.1000, close=1.1015),
    ]
    return candles, Quote(symbol="EUR_USD", bid=1.1014, ask=1.1016, time=now)


def test_max_position_block_does_not_create_a_review(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")
    # max_open_positions=0 forces the position-limit block path.
    orch = ExecutionOrchestrator(
        strategy=EurUsdOpeningWindowStrategy(max_spread_pips=2.0),
        risk_policy=RiskPolicy(0.0025, 0.01, 0),
        broker=SimulatedBroker(),
        repository=repo,
        equity=10_000,
        session_start_local="00:00", session_end_local="23:59", session_tz="UTC",
    )
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    candles, quote = _inputs(now)

    result = orch.run_cycle(candles=candles, quote=quote, now=now)

    assert result.status == "blocked"
    assert "open position" in result.reason.lower()
    # The block is still audited as a cycle, but creates no review noise.
    assert repo.list_cycles()[0]["status"] == "blocked"
    assert repo.list_reviews() == []


def test_meaningful_block_still_creates_a_review(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")
    # Risk-exceeded style block (tiny equity -> sizing/risk fails) still reviews.
    orch = ExecutionOrchestrator(
        strategy=EurUsdOpeningWindowStrategy(max_spread_pips=2.0),
        risk_policy=RiskPolicy(0.0025, 0.01, 1),
        broker=SimulatedBroker(),
        repository=repo,
        equity=10_000,
        session_start_local="00:00", session_end_local="09:00", session_tz="UTC",
    )
    # 20:00 UTC is outside the 00:00-09:00 window -> a meaningful block.
    now = datetime(2026, 6, 22, 20, 0, tzinfo=UTC)
    candles, quote = _inputs(now)

    orch.run_cycle(candles=candles, quote=quote, now=now)

    assert len(repo.list_reviews()) == 1  # session block is worth reviewing


def test_daily_loss_block_does_not_create_a_review(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")
    orch = ExecutionOrchestrator(
        strategy=EurUsdOpeningWindowStrategy(max_spread_pips=2.0),
        risk_policy=RiskPolicy(0.0025, 0.01, 1),
        broker=SimulatedBroker(),
        repository=repo,
        equity=10_000,
        session_start_local="00:00", session_end_local="23:59", session_tz="UTC",
    )
    orch.daily_realized_pnl = -100.0  # at the 1% daily-loss cap
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    candles, quote = _inputs(now)

    result = orch.run_cycle(candles=candles, quote=quote, now=now)

    assert result.status == "blocked"
    assert "daily loss" in result.reason.lower()
    assert repo.list_reviews() == []  # routine halt, no review noise
