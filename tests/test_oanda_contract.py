from datetime import datetime

from forex_trader.broker.oanda import OandaBroker


class FakeOandaBroker(OandaBroker):
    def __init__(self) -> None:
        super().__init__(mode="practice", account_id="acct", token="token")
        self.requests = []

    def _request(self, method, path, payload=None):
        self.requests.append((method, path, payload))
        if path.startswith("/v3/accounts/acct/pricing"):
            return {
                "prices": [
                    {
                        "bids": [{"price": "1.10000"}],
                        "asks": [{"price": "1.10020"}],
                        "time": "2026-06-22T12:00:00Z",
                    }
                ]
            }
        if path == "/v3/accounts/acct/orders":
            return {
                "orderFillTransaction": {
                    "id": "fill-1",
                    "orderID": "order-1",
                    "price": "1.10020",
                }
            }
        if path == "/v3/accounts/acct/openPositions":
            return {"positions": []}
        if path == "/v3/accounts/acct/positions/EUR_USD/close":
            return {"longOrderFillTransaction": {"price": "1.10100"}}
        raise AssertionError(path)


def test_oanda_quote_and_order_request_shapes():
    broker = FakeOandaBroker()

    quote = broker.get_quote("EUR_USD")
    order = broker.place_market_order(
        symbol="EUR_USD",
        side="buy",
        units=1000,
        price=quote.ask,
        stop_loss=1.0990,
        take_profit=1.1030,
        opened_at=datetime.fromisoformat("2026-06-22T12:00:00+00:00"),
    )

    assert quote.bid == 1.1000
    assert order.order_id == "order-1"
    assert broker.requests[1][2]["order"]["stopLossOnFill"]["price"] == "1.09900"


def test_oanda_close_position_uses_position_close_endpoint():
    broker = FakeOandaBroker()

    closed = broker.close_position(
        "EUR_USD",
        price=1.1010,
        closed_at=datetime.fromisoformat("2026-06-22T12:10:00+00:00"),
    )

    assert closed.symbol == "EUR_USD"
    assert closed.close_price == 1.1010
    assert broker.requests[0][0] == "PUT"
