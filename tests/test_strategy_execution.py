from datetime import UTC, datetime

from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote
from forex_trader.execution.orchestrator import ExecutionOrchestrator
from forex_trader.research.registry import ResearchRegistry
from forex_trader.risk.policy import RiskPolicy
from forex_trader.storage.repositories import TradingRepository
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy
from forex_trader.strategy.selector import select_strategy


def test_non_ready_strategy_selection_returns_null_strategy():
    registry = ResearchRegistry()

    strategy = select_strategy(registry, "eurusd_opening_window")

    assert strategy.evaluate([], None) is None


def test_opening_window_strategy_emits_trade_plan_when_breakout_is_valid():
    strategy = EurUsdOpeningWindowStrategy(max_spread_pips=2.0)
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    candles = [
        Candle(time=now, open=1.1000, high=1.1010, low=1.0990, close=1.1005),
        Candle(time=now, open=1.1005, high=1.1020, low=1.1000, close=1.1015),
    ]
    quote = Quote(symbol="EUR_USD", bid=1.1014, ask=1.1016, time=now)

    signal = strategy.evaluate(candles, quote)

    assert signal is not None
    assert signal.side == OrderSide.BUY
    assert signal.stop_loss == 1.0990
    assert signal.take_profit > signal.entry_price


def test_orchestrator_persists_blocked_trade_with_review(tmp_path):
    repository = TradingRepository(tmp_path / "trades.db")
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.01, max_open_positions=0)
    strategy = EurUsdOpeningWindowStrategy(max_spread_pips=2.0)
    broker = SimulatedBroker()
    orchestrator = ExecutionOrchestrator(
        strategy=strategy,
        risk_policy=policy,
        broker=broker,
        repository=repository,
        equity=10_000,
    )
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    candles = [
        Candle(time=now, open=1.1000, high=1.1010, low=1.0990, close=1.1005),
        Candle(time=now, open=1.1005, high=1.1020, low=1.1000, close=1.1015),
    ]
    quote = Quote(symbol="EUR_USD", bid=1.1014, ask=1.1016, time=now)

    result = orchestrator.run_cycle(candles=candles, quote=quote, now=now)

    assert result.status == "blocked"
    assert "open position" in result.reason.lower()
    assert repository.list_cycles()[0]["status"] == "blocked"
    assert repository.list_reviews()[0]["outcome"] == "blocked"


def test_orchestrator_places_approved_trade_and_persists_order(tmp_path):
    repository = TradingRepository(tmp_path / "trades.db")
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.01, max_open_positions=1)
    strategy = EurUsdOpeningWindowStrategy(max_spread_pips=2.0)
    broker = SimulatedBroker()
    orchestrator = ExecutionOrchestrator(
        strategy=strategy,
        risk_policy=policy,
        broker=broker,
        repository=repository,
        equity=10_000,
    )
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    candles = [
        Candle(time=now, open=1.1000, high=1.1010, low=1.0990, close=1.1005),
        Candle(time=now, open=1.1005, high=1.1020, low=1.1000, close=1.1015),
    ]
    quote = Quote(symbol="EUR_USD", bid=1.1014, ask=1.1016, time=now)

    result = orchestrator.run_cycle(candles=candles, quote=quote, now=now)

    assert result.status == "ordered"
    assert broker.list_open_positions()
    assert repository.list_cycles()[0]["status"] == "ordered"


def test_orchestrator_force_closes_expired_positions(tmp_path):
    repository = TradingRepository(tmp_path / "trades.db")
    broker = SimulatedBroker()
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.01, max_open_positions=1)
    orchestrator = ExecutionOrchestrator(
        strategy=EurUsdOpeningWindowStrategy(),
        risk_policy=policy,
        broker=broker,
        repository=repository,
        equity=10_000,
        max_hold_minutes=30,
    )
    opened_at = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    order = broker.place_market_order(
        symbol="EUR_USD",
        side="buy",
        units=10_000,
        price=1.1000,
        stop_loss=1.0990,
        take_profit=1.1020,
        opened_at=opened_at,
    )

    closed = orchestrator.close_expired_positions(
        now=datetime(2026, 6, 22, 12, 31, tzinfo=UTC),
        price=1.1010,
        session_end_local="23:59",
    )

    assert [position.position_id for position in closed] == [order.position_id]
    assert broker.list_open_positions() == []
