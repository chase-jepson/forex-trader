"""Split candles into in-sample and out-of-sample by date."""
from datetime import UTC, datetime

from forex_trader.backtest.split import split_by_date
from forex_trader.domain.models import Candle


def _c(day):
    return Candle(time=datetime(2026, day // 30 + 1, day % 30 + 1, tzinfo=UTC),
                  open=1.1, high=1.1, low=1.1, close=1.1)


def test_split_partitions_before_and_after_the_date():
    candles = [
        Candle(time=datetime(2026, 4, 1, tzinfo=UTC), open=1, high=1, low=1, close=1),
        Candle(time=datetime(2026, 5, 1, tzinfo=UTC), open=1, high=1, low=1, close=1),
        Candle(time=datetime(2026, 6, 1, tzinfo=UTC), open=1, high=1, low=1, close=1),
    ]

    in_sample, out_sample = split_by_date(candles, split=datetime(2026, 5, 15, tzinfo=UTC))

    assert [c.time.month for c in in_sample] == [4, 5]
    assert [c.time.month for c in out_sample] == [6]


def test_split_midpoint_helper():
    from forex_trader.backtest.split import midpoint_date

    candles = [
        Candle(time=datetime(2026, 4, 1, tzinfo=UTC), open=1, high=1, low=1, close=1),
        Candle(time=datetime(2026, 6, 1, tzinfo=UTC), open=1, high=1, low=1, close=1),
    ]
    mid = midpoint_date(candles)
    assert datetime(2026, 4, 1, tzinfo=UTC) < mid < datetime(2026, 6, 1, tzinfo=UTC)
