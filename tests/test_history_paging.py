"""Multi-page OANDA history fetch assembles an arbitrary date range."""
from datetime import UTC, datetime, timedelta

from forex_trader.backtest.history_fetch import OandaHistoryFetcher


def _candle(dt, price=1.10):
    ts = dt.isoformat().replace("+00:00", "Z")
    return {"time": ts, "complete": True,
            "mid": {"o": str(price), "h": str(price + 0.001),
                    "l": str(price - 0.001), "c": str(price)}}


class _FakeFetcher(OandaHistoryFetcher):
    """Simulates OANDA: returns `count` hourly candles ending at `to_time`,
    but no data older than EARLIEST."""
    EARLIEST = datetime(2026, 1, 1, tzinfo=UTC)

    def __init__(self):
        super().__init__(token="tok")
        self.calls = []

    def _request_candles(self, *, granularity, count, to_time):
        self.calls.append(to_time)
        end = (
            datetime.fromisoformat(to_time.replace("Z", "+00:00"))
            if to_time else datetime(2026, 6, 2, tzinfo=UTC)
        )
        # Return up to 1000 hourly candles before `end` (a realistic large
        # page), none earlier than EARLIEST.
        out = []
        for i in range(1, 1001):
            t = end - timedelta(hours=i)
            if t < self.EARLIEST:
                break
            out.append(_candle(t))
        return list(reversed(out))


def test_fetch_range_pages_backward_and_dedups_sorted():
    fetcher = _FakeFetcher()

    # ~90 days > one 1000-hour (~41-day) page, so paging is required.
    start = datetime(2026, 3, 4, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)
    candles = fetcher.fetch_range(granularity="H1", start=start, end=end)

    assert len(fetcher.calls) >= 2  # needed multiple pages
    times = [c.time for c in candles]
    assert times == sorted(times)              # ascending
    assert len(times) == len(set(times))       # deduped
    assert all(start <= t <= end for t in times)


def test_fetch_range_stops_when_no_older_data():
    fetcher = _FakeFetcher()
    candles = fetcher.fetch_range(
        granularity="H1",
        start=datetime(2026, 1, 1, tzinfo=UTC),  # earlier than any data
        end=datetime(2026, 6, 2, tzinfo=UTC),
    )
    assert len(candles) > 0
    assert len(fetcher.calls) < 200  # terminated, didn't hit the page backstop
