"""Structured logging helper — consistent format, never logs secrets."""
import logging

from forex_trader.obs.logging import get_logger, redact


def test_get_logger_returns_namespaced_logger():
    logger = get_logger("execution")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "forex_trader.execution"


def test_get_logger_is_idempotent_no_duplicate_handlers():
    a = get_logger("dup")
    handlers_before = len(a.handlers)
    b = get_logger("dup")
    assert a is b
    assert len(b.handlers) == handlers_before


def test_redact_masks_token_like_values():
    token = "1b5a1286f14a2856a69b2e4fd73082a4-920e5e1a9e495506d31f78b8247dd4e6"
    msg = f"calling OANDA with Bearer {token}"

    cleaned = redact(msg, secrets=[token])

    assert token not in cleaned
    assert "REDACTED" in cleaned


def test_redact_ignores_empty_secrets():
    # Empty/blank secrets must not turn into a redact-everything bug.
    msg = "normal message"
    assert redact(msg, secrets=["", None]) == msg
