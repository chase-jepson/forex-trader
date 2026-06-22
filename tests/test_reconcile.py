"""Reconcile broker-reported positions against locally expected count."""
from datetime import UTC, datetime

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Position
from forex_trader.execution.reconcile import reconcile_positions


def _pos(pid):
    return Position(
        position_id=pid, symbol="EUR_USD", side=OrderSide.BUY, units=1000,
        entry_price=1.1, stop_loss=1.09, take_profit=1.11,
        opened_at=datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
    )


def test_in_sync_when_counts_match():
    result = reconcile_positions(broker_positions=[_pos("a")], expected_open=1)
    assert result.in_sync is True
    assert result.broker_count == 1


def test_out_of_sync_when_broker_has_more_than_expected():
    result = reconcile_positions(broker_positions=[_pos("a"), _pos("b")], expected_open=1)
    assert result.in_sync is False
    assert "2" in result.reason and "1" in result.reason


def test_out_of_sync_when_broker_has_fewer_than_expected():
    result = reconcile_positions(broker_positions=[], expected_open=1)
    assert result.in_sync is False
