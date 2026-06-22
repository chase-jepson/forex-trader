"""OANDA health check — read-only account summary."""
from forex_trader.broker.oanda import OandaBroker


class _FakeHealthBroker(OandaBroker):
    def __init__(self, response):
        super().__init__(mode="practice", account_id="acct", token="tok")
        self._response = response
        self.requests = []

    def _request(self, method, path, payload=None):
        self.requests.append((method, path))
        return self._response


def test_health_check_returns_ok_with_balance_and_currency():
    broker = _FakeHealthBroker(
        {"account": {"balance": "100000.0000", "currency": "USD", "openTradeCount": 0}}
    )

    health = broker.health_check()

    assert health.ok is True
    assert health.balance == 100000.0
    assert health.currency == "USD"
    assert broker.requests[0] == ("GET", "/v3/accounts/acct/summary")


def test_health_check_flags_missing_account_block():
    broker = _FakeHealthBroker({"errorMessage": "Insufficient authorization"})

    health = broker.health_check()

    assert health.ok is False
    assert "authorization" in health.reason.lower()
