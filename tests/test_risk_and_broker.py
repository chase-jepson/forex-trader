from datetime import UTC, datetime

from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.risk.policy import RiskPolicy
from forex_trader.risk.sizing import calculate_units_for_risk


def test_risk_policy_rejects_trade_without_stop_loss():
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.01, max_open_positions=1)

    decision = policy.validate_trade(
        equity=10_000,
        open_positions=0,
        stop_loss_pips=None,
        take_profit=1.1050,
        risk_amount=25,
        max_hold_minutes=90,
    )

    assert decision.approved is False
    assert "stop" in decision.reason.lower()


def test_risk_policy_rejects_trade_above_default_risk_limit():
    policy = RiskPolicy(max_risk_per_trade=0.0025, max_daily_loss=0.01, max_open_positions=1)

    decision = policy.validate_trade(
        equity=10_000,
        open_positions=0,
        stop_loss_pips=10,
        take_profit=1.1050,
        risk_amount=26,
        max_hold_minutes=90,
    )

    assert decision.approved is False
    assert "0.25%" in decision.reason


def test_position_sizing_uses_equity_risk_and_stop_distance():
    units = calculate_units_for_risk(equity=10_000, max_risk_fraction=0.0025, stop_loss_pips=10)

    assert units == 25_000


def test_simulated_broker_opens_closes_and_calculates_pnl():
    # With a 1-pip half-spread the buy fills at 1.1001 (ask) and the close at
    # 1.1009 (bid), so a 10-pip mid move nets 8 pips after the spread cost.
    broker = SimulatedBroker(half_spread_pips=1.0)
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
    closed = broker.close_position(order.position_id, price=1.1010, closed_at=opened_at)

    assert order.accepted is True
    assert broker.list_open_positions() == []
    assert round(closed.realized_pnl, 2) == 8.0

