from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from typing import Any
from urllib import error, request

from forex_trader.domain.models import PIP_SIZE, Candle

PRACTICE_CANDLES_URL = (
    "https://api-fxpractice.oanda.com/v3/instruments/{instrument}/candles"
    "?count={count}&granularity={granularity}&price=M"
)


def parse_oanda_candles(payload: dict[str, Any]) -> list[Candle]:
    """Map an OANDA candles response to domain Candles, skipping incomplete ones."""
    candles: list[Candle] = []
    for item in payload.get("candles", []):
        if not item.get("complete", False):
            continue  # a forming candle is not yet final
        mid = item["mid"]
        candles.append(
            Candle(
                time=datetime.fromisoformat(item["time"].replace("Z", "+00:00")),
                open=float(mid["o"]),
                high=float(mid["h"]),
                low=float(mid["l"]),
                close=float(mid["c"]),
                volume=int(item.get("volume", 0)),
            )
        )
    return candles


def fetch_oanda_candles(
    *,
    token: str,
    instrument: str = "EUR_USD",
    count: int = 500,
    granularity: str = "M1",
) -> list[Candle]:
    """Fetch real historical candles from the OANDA practice API.

    Credential-gated: callers must supply a valid practice token. Read-only.
    """
    url = PRACTICE_CANDLES_URL.format(
        instrument=instrument, count=count, granularity=granularity
    )
    req = request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with request.urlopen(req, timeout=15) as response:  # noqa: S310 - fixed OANDA host
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OANDA candles fetch failed: HTTP {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"OANDA candles fetch network error: {exc.reason}") from exc
    return parse_oanda_candles(payload)


def resolve_candle_source(
    *,
    use_real: bool,
    token: str,
    days: int,
    seed: int,
    granularity: str = "M5",
    count: int = 5000,
) -> list[Candle]:
    """Return candles for a backtest: real OANDA history or the offline fixture.

    With `use_real`, fetches real EUR/USD candles from OANDA (requires a token).
    Otherwise generates the deterministic offline fixture.
    """
    if use_real:
        if not token:
            raise ValueError("Real candles require an OANDA token (set OANDA_API_TOKEN).")
        return fetch_oanda_candles(token=token, count=count, granularity=granularity)
    from datetime import datetime

    return realistic_session_candles(
        start=datetime.fromisoformat("2026-06-01T00:00:00+00:00"), days=days, seed=seed
    )


def realistic_session_candles(
    *,
    start: datetime,
    days: int,
    seed: int = 0,
    start_price: float = 1.1000,
    minutes_per_day: int = 24 * 60,
    base_volatility_pips: float = 3.0,
) -> list[Candle]:
    """Deterministic offline EUR/USD fixture with intraday session structure.

    A seeded random walk whose volatility rises during the European/US overlap
    (roughly 12:00-16:00 UTC) and falls overnight, so backtests exercise
    session-aware behavior without a network dependency. Labeled clearly as a
    fixture: it is NOT real market data and implies no edge.
    """
    rng = random.Random(seed)
    candles: list[Candle] = []
    price = start_price
    total_minutes = days * minutes_per_day
    for index in range(total_minutes):
        stamp = start + timedelta(minutes=index)
        # Higher volatility during the active overlap window.
        active = 12 <= stamp.hour < 16
        vol = base_volatility_pips * (1.8 if active else 0.6) * PIP_SIZE
        drift = rng.uniform(-vol, vol)
        open_price = price
        close_price = max(0.0001, open_price + drift)
        wick = abs(rng.uniform(0, vol))
        high = max(open_price, close_price) + wick
        low = min(open_price, close_price) - wick
        candles.append(
            Candle(
                time=stamp,
                open=round(open_price, 5),
                high=round(high, 5),
                low=round(low, 5),
                close=round(close_price, 5),
            )
        )
        price = close_price
    return candles
