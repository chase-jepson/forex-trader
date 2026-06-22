"""Simulated broker must model realistic fill costs so PnL is not optimistic."""
from datetime import UTC, datetime

from forex_trader.broker.simulated import SimulatedBroker
from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Quote


def test_buy_fills_at_ask_when_requested_price_is_mid():
    # With slippage modeling, a buy should fill at the ask, not the mid.
    broker = SimulatedBroker(half_spread_pips=1.0)
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    broker.set_quote(Quote(symbol="EUR_USD", bid=1.0999, ask=1.1001, time=now))

    order = broker.place_market_order(
        symbol="EUR_USD",
        side="buy",
        units=10_000,
        price=1.1000,  # mid requested
        stop_loss=1.0980,
        take_profit=1.1040,
        opened_at=now,
    )

    # Buy filled at ask = mid + 1 pip
    assert round(order.fill_price, 4) == 1.1001


def test_sell_fills_at_bid_when_requested_price_is_mid():
    broker = SimulatedBroker(half_spread_pips=1.0)
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    broker.set_quote(Quote(symbol="EUR_USD", bid=1.0999, ask=1.1001, time=now))

    order = broker.place_market_order(
        symbol="EUR_USD",
        side="sell",
        units=10_000,
        price=1.1000,
        stop_loss=1.1020,
        take_profit=1.0960,
        opened_at=now,
    )

    assert round(order.fill_price, 4) == 1.0999


def test_round_trip_with_unchanged_mid_loses_the_spread():
    broker = SimulatedBroker(half_spread_pips=1.0)
    now = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    broker.set_quote(Quote(symbol="EUR_USD", bid=1.0999, ask=1.1001, time=now))

    order = broker.place_market_order(
        symbol="EUR_USD",
        side="buy",
        units=10_000,
        price=1.1000,
        stop_loss=1.0980,
        take_profit=1.1040,
        opened_at=now,
    )
    # Close at the prevailing bid (what a seller receives), unchanged mid.
    closed = broker.close_position(order.position_id, price=None, closed_at=now)

    # Bought at ask 1.1001, exit at bid 1.0999 -> 2 pip loss on 10k = -$2.00
    assert round(closed.realized_pnl, 2) == -2.00
    assert closed.side == OrderSide.BUY
