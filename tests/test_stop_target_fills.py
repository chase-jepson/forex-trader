"""Open positions must be resolved against intra-bar stop/target hits."""
from datetime import UTC, datetime

from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.domain.models import Candle
from forex_trader.execution.orchestrator import ExecutionOrchestrator
from forex_trader.risk.policy import RiskPolicy
from forex_trader.storage.repositories import TradingRepository
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


def _orch(tmp_path, broker):
    return ExecutionOrchestrator(
        strategy=EurUsdOpeningWindowStrategy(),
        risk_policy=RiskPolicy(0.0025, 0.01, 1),
        broker=broker,
        repository=TradingRepository(tmp_path / "t.db"),
        equity=10_000,
        session_tz="UTC",
    )


def test_long_position_closes_at_stop_when_candle_low_breaches_it(tmp_path):
    broker = SimulatedBroker(half_spread_pips=0.0)
    orch = _orch(tmp_path, broker)
    opened = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    broker.place_market_order(
        symbol="EUR_USD", side="buy", units=10_000, price=1.1000,
        stop_loss=1.0990, take_profit=1.1030, opened_at=opened,
    )
    # Candle dips to 1.0985 (below stop 1.0990) then recovers.
    candle = Candle(time=opened, open=1.1000, high=1.1005, low=1.0985, close=1.1000)

    closed = orch.resolve_stop_target_fills(candle=candle, now=opened)

    assert len(closed) == 1
    assert closed[0].close_price == 1.0990  # filled at stop
    assert not broker.list_open_positions()
    reviews = orch.repository.list_reviews()
    assert reviews[0]["outcome"] == "loss"


def test_long_position_closes_at_target_when_candle_high_breaches_it(tmp_path):
    broker = SimulatedBroker(half_spread_pips=0.0)
    orch = _orch(tmp_path, broker)
    opened = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    broker.place_market_order(
        symbol="EUR_USD", side="buy", units=10_000, price=1.1000,
        stop_loss=1.0990, take_profit=1.1030, opened_at=opened,
    )
    candle = Candle(time=opened, open=1.1000, high=1.1035, low=1.0998, close=1.1030)

    closed = orch.resolve_stop_target_fills(candle=candle, now=opened)

    assert closed[0].close_price == 1.1030  # filled at target
    assert orch.repository.list_reviews()[0]["outcome"] == "win"


def test_no_fill_when_candle_stays_between_stop_and_target(tmp_path):
    broker = SimulatedBroker(half_spread_pips=0.0)
    orch = _orch(tmp_path, broker)
    opened = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    broker.place_market_order(
        symbol="EUR_USD", side="buy", units=10_000, price=1.1000,
        stop_loss=1.0990, take_profit=1.1030, opened_at=opened,
    )
    candle = Candle(time=opened, open=1.1000, high=1.1010, low=1.0995, close=1.1005)

    closed = orch.resolve_stop_target_fills(candle=candle, now=opened)

    assert closed == []
    assert len(broker.list_open_positions()) == 1


def test_short_position_closes_at_stop_when_candle_high_breaches_it(tmp_path):
    broker = SimulatedBroker(half_spread_pips=0.0)
    orch = _orch(tmp_path, broker)
    opened = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    broker.place_market_order(
        symbol="EUR_USD", side="sell", units=10_000, price=1.1000,
        stop_loss=1.1010, take_profit=1.0970, opened_at=opened,
    )
    candle = Candle(time=opened, open=1.1000, high=1.1015, low=1.0998, close=1.1005)

    closed = orch.resolve_stop_target_fills(candle=candle, now=opened)

    assert closed[0].close_price == 1.1010  # short stop
    assert orch.repository.list_reviews()[0]["outcome"] == "loss"
