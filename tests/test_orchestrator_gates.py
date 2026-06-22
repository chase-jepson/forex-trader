"""Orchestrator must enforce session window, daily-loss cap, and scratch exits."""
from datetime import UTC, datetime

from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.domain.models import Candle, Quote
from forex_trader.execution.orchestrator import ExecutionOrchestrator
from forex_trader.risk.policy import RiskPolicy
from forex_trader.storage.repositories import TradingRepository
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


def _breakout_inputs(now):
    candles = [
        Candle(time=now, open=1.1000, high=1.1010, low=1.0990, close=1.1005),
        Candle(time=now, open=1.1005, high=1.1020, low=1.1000, close=1.1015),
    ]
    quote = Quote(symbol="EUR_USD", bid=1.1014, ask=1.1016, time=now)
    return candles, quote


def _orchestrator(tmp_path, broker, **kwargs):
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.01, max_open_positions=1)
    return ExecutionOrchestrator(
        strategy=EurUsdOpeningWindowStrategy(max_spread_pips=2.0),
        risk_policy=policy,
        broker=broker,
        repository=TradingRepository(tmp_path / "t.db"),
        equity=10_000,
        **kwargs,
    )


def test_blocks_entry_outside_session_window(tmp_path):
    broker = SimulatedBroker()
    orch = _orchestrator(
        tmp_path, broker,
        session_start_local="05:00", session_end_local="09:00",
        session_tz="America/Mexico_City",
    )
    # 20:00 UTC = 14:00 local, well outside the morning window.
    now = datetime(2026, 6, 22, 20, 0, tzinfo=UTC)
    candles, quote = _breakout_inputs(now)

    result = orch.run_cycle(candles=candles, quote=quote, now=now)

    assert result.status == "blocked"
    assert "session" in result.reason.lower()
    assert not broker.list_open_positions()


def test_blocks_entry_when_daily_loss_cap_reached(tmp_path):
    broker = SimulatedBroker()
    orch = _orchestrator(
        tmp_path, broker,
        session_start_local="00:00", session_end_local="23:59",
    )
    orch.daily_realized_pnl = -100.0  # equity 10k * 1% cap = -100 -> at the cap
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    candles, quote = _breakout_inputs(now)

    result = orch.run_cycle(candles=candles, quote=quote, now=now)

    assert result.status == "blocked"
    assert "daily loss" in result.reason.lower()


def test_flat_forced_exit_is_recorded_as_scratch(tmp_path):
    broker = SimulatedBroker(half_spread_pips=0.0)  # no spread so a flat exit nets zero
    orch = _orchestrator(tmp_path, broker, max_hold_minutes=30)
    opened = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    broker.set_quote(Quote(symbol="EUR_USD", bid=1.1000, ask=1.1000, time=opened))
    broker.place_market_order(
        symbol="EUR_USD", side="buy", units=10_000, price=1.1000,
        stop_loss=1.0990, take_profit=1.1020, opened_at=opened,
    )

    closed = orch.close_expired_positions(
        now=datetime(2026, 6, 22, 12, 31, tzinfo=UTC),
        price=None,
        session_end_local="23:59",
    )

    assert len(closed) == 1
    reviews = orch.repository.list_reviews()
    assert reviews[0]["outcome"] == "scratch"
