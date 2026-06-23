from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib import error, request

from forex_trader.backtest.history import parse_oanda_candles
from forex_trader.domain.models import Candle

_MAX_PER_REQUEST = 5000
_MAX_PAGES = 200  # backstop so a bad range can never loop forever


class OandaHistoryFetcher:
    """Assemble an arbitrary EUR/USD date range from OANDA by paging backward.

    A single OANDA request caps at 5000 candles. To cover months of history we
    walk backward using the `to=` parameter, page by page, until we pass the
    requested start or run out of data.
    """

    PRACTICE_URL = "https://api-fxpractice.oanda.com"

    def __init__(self, *, token: str, instrument: str = "EUR_USD") -> None:
        self.token = token
        self.instrument = instrument

    def _request_candles(
        self, *, granularity: str, count: int, to_time: str | None
    ) -> list[dict[str, Any]]:
        url = (
            f"{self.PRACTICE_URL}/v3/instruments/{self.instrument}/candles"
            f"?granularity={granularity}&count={count}&price=M"
        )
        if to_time is not None:
            url += f"&to={to_time}"
        req = request.Request(url, headers={"Authorization": f"Bearer {self.token}"})
        try:
            with request.urlopen(req, timeout=20) as response:  # noqa: S310 - fixed OANDA host
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OANDA history fetch failed: HTTP {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OANDA history fetch network error: {exc.reason}") from exc
        result = payload.get("candles", [])
        return list(result)

    def fetch_range(
        self,
        *,
        granularity: str,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        """Fetch all complete candles in [start, end], paging backward."""
        by_time: dict[datetime, Candle] = {}
        to_time: str | None = _to_param(end)
        prev_oldest: datetime | None = None
        for _ in range(_MAX_PAGES):
            raw = self._request_candles(
                granularity=granularity, count=_MAX_PER_REQUEST, to_time=to_time
            )
            page = parse_oanda_candles({"candles": raw})
            if not page:
                break
            for candle in page:
                if start <= candle.time <= end:
                    by_time[candle.time] = candle
            oldest = min(c.time for c in page)
            if oldest <= start:
                break  # covered the whole requested range
            if prev_oldest is not None and oldest >= prev_oldest:
                break  # not advancing backward — we've hit the data floor
            prev_oldest = oldest
            to_time = _to_param(oldest)

        return [by_time[t] for t in sorted(by_time)]


def _to_param(when: datetime) -> str:
    """Format a datetime for OANDA's `to=` parameter (RFC3339, Z suffix)."""
    return when.isoformat().replace("+00:00", "Z")
