"""Orchestrator persists a trade story on open and updates it on close."""
from datetime import UTC, datetime

from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.domain.models import Candle, Quote
from forex_trader.execution.orchestrator import ExecutionOrchestrator
from forex_trader.risk.policy import RiskPolicy
from forex_trader.storage.repositories import TradingRepository
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


def _setup(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")
    broker = SimulatedBroker(half_spread_pips=0.0)
    orch = ExecutionOrchestrator(
        strategy=EurUsdOpeningWindowStrategy(max_spread_pips=2.0),
        risk_policy=RiskPolicy(0.0025, 0.01, 1),
        broker=broker,
        repository=repo,
        equity=10_000,
        max_hold_minutes=30,
        session_start_local="00:00",
        session_end_local="23:59",
        session_tz="UTC",
    )
    return repo, broker, orch


def _inputs(now):
    candles = [
        Candle(time=now, open=1.1000, high=1.1010, low=1.0990, close=1.1005),
        Candle(time=now, open=1.1005, high=1.1020, low=1.1000, close=1.1015),
    ]
    return candles, Quote(symbol="EUR_USD", bid=1.1014, ask=1.1016, time=now)


def test_approved_trade_writes_a_story_with_context_and_reasoning(tmp_path):
    repo, broker, orch = _setup(tmp_path)
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    candles, quote = _inputs(now)

    result = orch.run_cycle(candles=candles, quote=quote, now=now)

    assert result.status == "ordered"
    stories = repo.list_trade_stories()
    assert len(stories) == 1
    story = stories[0]
    assert story["side"] == "buy"
    assert story["signal_reason"]  # captured the why
    assert len(story["context_candles"]) == 2  # captured pre-entry candles
    assert story["outcome"] == "open"


def test_forced_close_updates_the_story_to_closed(tmp_path):
    repo, broker, orch = _setup(tmp_path)
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    candles, quote = _inputs(now)
    orch.run_cycle(candles=candles, quote=quote, now=now)

    orch.close_expired_positions(
        now=datetime(2026, 6, 22, 12, 31, tzinfo=UTC), price=None,
        session_end_local="23:59",
    )

    story = repo.list_trade_stories()[0]
    assert story["outcome"] in {"win", "loss", "scratch"}
    assert story["closed_at"] is not None
    assert story["exit_reason"]
