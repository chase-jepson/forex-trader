"""LiveTrader.tick — safety-gated single cycle, tested with a fake broker (no network)."""
from datetime import UTC, datetime

from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.domain.models import Candle, Quote
from forex_trader.execution.live import LiveTrader
from forex_trader.risk.policy import RiskPolicy
from forex_trader.storage.repositories import TradingRepository
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


def _candles(now):
    return [
        Candle(time=now, open=1.1000, high=1.1010, low=1.0990, close=1.1005),
        Candle(time=now, open=1.1005, high=1.1020, low=1.1000, close=1.1015),
    ]


def _trader(tmp_path, broker, *, armed, stop_path=None):
    return LiveTrader(
        strategy=EurUsdOpeningWindowStrategy(max_spread_pips=2.0),
        risk_policy=RiskPolicy(0.0025, 0.01, 1),
        broker=broker,
        repository=TradingRepository(tmp_path / "live.db"),
        equity=10_000,
        armed=armed,
        emergency_stop_path=str(stop_path) if stop_path else str(tmp_path / "NOSTOP"),
        session_start_local="00:00", session_end_local="23:59", session_tz="UTC",
    )


def test_tick_blocks_all_action_when_emergency_stopped(tmp_path):
    stop = tmp_path / "STOP"
    stop.write_text("halt")
    broker = SimulatedBroker()
    trader = _trader(tmp_path, broker, armed=True, stop_path=stop)
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)

    result = trader.tick(candles=_candles(now), quote=_q(now), now=now)

    assert result.status == "halted"
    assert not broker.list_open_positions()


def test_dry_run_does_not_place_orders_even_on_a_valid_signal(tmp_path):
    broker = SimulatedBroker()
    trader = _trader(tmp_path, broker, armed=False)
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)

    result = trader.tick(candles=_candles(now), quote=_q(now), now=now)

    assert result.status == "dry_run"
    assert not broker.list_open_positions()  # nothing actually placed


def test_armed_tick_places_order_on_valid_signal(tmp_path):
    broker = SimulatedBroker()
    trader = _trader(tmp_path, broker, armed=True)
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)

    result = trader.tick(candles=_candles(now), quote=_q(now), now=now)

    assert result.status == "ordered"
    assert broker.list_open_positions()


def _q(now):
    return Quote(symbol="EUR_USD", bid=1.1014, ask=1.1016, time=now)
