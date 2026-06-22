from __future__ import annotations

import logging

_CONFIGURED: set[str] = set()
_FORMAT = "%(asctime)s %(levelname)-7s %(name)s %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under `forex_trader.*` with a single handler.

    Idempotent: calling it repeatedly for the same name never stacks handlers.
    """
    full_name = f"forex_trader.{name}"
    logger = logging.getLogger(full_name)
    if full_name not in _CONFIGURED:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        _CONFIGURED.add(full_name)
    return logger


def redact(message: str, secrets: list[str | None]) -> str:
    """Replace any non-empty secret occurrence in `message` with [REDACTED].

    Empty or None secrets are ignored so a blank credential cannot accidentally
    redact the entire message.
    """
    cleaned = message
    for secret in secrets:
        if secret:
            cleaned = cleaned.replace(secret, "[REDACTED]")
    return cleaned
