"""Credential-gated OANDA practice integration tests.

These hit the real fxPractice endpoint and are skipped unless OANDA practice
credentials are present in the environment (.env). They are READ-ONLY: pricing
and account inspection only — no orders are placed.
"""
import pytest

from forex_trader.config import Settings

settings = Settings.from_env()
_HAVE_CREDS = bool(settings.oanda_account_id and settings.oanda_api_token)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _HAVE_CREDS, reason="OANDA practice credentials not configured"),
]


def _broker():
    from forex_trader.broker.oanda import OandaBroker

    return OandaBroker(
        mode="practice",
        account_id=settings.oanda_account_id,
        token=settings.oanda_api_token,
    )


def test_practice_pricing_fetch_returns_live_quote():
    quote = _broker().get_quote("EUR_USD")

    assert quote.symbol == "EUR_USD"
    assert quote.ask >= quote.bid > 0
    assert quote.spread_pips >= 0


def test_practice_open_positions_is_listable():
    # Read-only: just confirm the account's open positions can be listed.
    positions = _broker().list_open_positions()

    assert isinstance(positions, list)
