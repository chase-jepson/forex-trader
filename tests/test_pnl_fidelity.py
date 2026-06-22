"""Sizing and PnL must reconcile through a single pip-value model.

If a position is sized to risk exactly `risk_amount` at its stop distance,
then closing at the stop must realize approximately `-risk_amount`.
"""
from datetime import UTC, datetime

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import PIP_SIZE, Position
from forex_trader.risk.sizing import PIP_VALUE_PER_UNIT, calculate_units_for_risk


def test_closing_at_stop_realizes_negative_risk_amount():
    equity = 10_000.0
    risk_fraction = 0.0025  # $25
    stop_loss_pips = 10.0
    entry = 1.1000
    stop = entry - stop_loss_pips * PIP_SIZE  # long, stop below entry

    units = calculate_units_for_risk(
        equity=equity,
        max_risk_fraction=risk_fraction,
        stop_loss_pips=stop_loss_pips,
    )
    position = Position(
        position_id="p1",
        symbol="EUR_USD",
        side=OrderSide.BUY,
        units=units,
        entry_price=entry,
        stop_loss=stop,
        take_profit=entry + 0.0020,
        opened_at=datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
    )

    closed = position.close(price=stop)

    expected_risk = equity * risk_fraction  # -25.0
    assert round(closed.realized_pnl, 2) == round(-expected_risk, 2)


def test_pip_value_constant_is_shared_between_sizing_and_pnl():
    # PnL per pip per unit must equal the constant sizing uses.
    units = 1
    entry = 1.1000
    one_pip_up = entry + PIP_SIZE
    position = Position(
        position_id="p2",
        symbol="EUR_USD",
        side=OrderSide.BUY,
        units=units,
        entry_price=entry,
        stop_loss=1.0,
        take_profit=2.0,
        opened_at=datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
    )
    closed = position.close(price=one_pip_up)
    assert round(closed.realized_pnl, 8) == round(units * PIP_VALUE_PER_UNIT, 8)
