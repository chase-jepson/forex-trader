"""Opening-range breakout: trade a clean expansion from a tight opening range."""
from datetime import UTC, datetime, timedelta

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote
from forex_trader.strategy.eurusd_opening_range_breakout import (
    EurUsdOpeningRangeBreakoutStrategy,
)


def _candles(rows):
    start = datetime(2026, 6, 1, 12, 30, tzinfo=UTC)
    out = []
    for i, (hi, lo, cl) in enumerate(rows):
        out.append(Candle(time=start + timedelta(minutes=5 * i), open=cl,
                          high=hi, low=lo, close=cl, volume=1000))
    return out


def test_buys_on_break_above_tight_opening_range():
    strat = EurUsdOpeningRangeBreakoutStrategy(range_candles=6, max_range_pips=15.0,
                                               max_spread_pips=2.0)
    # 6 tight candles forming a ~10p range around 1.1000, then a break above.
    rows = [(1.1005, 1.0995, 1.1000)] * 6 + [(1.1012, 1.1006, 1.1010)]
    quote = Quote(symbol="EUR_USD", bid=1.1009, ask=1.1011, time=_candles(rows)[-1].time)

    signal = strat.evaluate(_candles(rows), quote)
    assert signal is not None
    assert signal.side == OrderSide.BUY
    assert signal.take_profit > signal.entry_price


def test_sells_on_break_below():
    strat = EurUsdOpeningRangeBreakoutStrategy(range_candles=6, max_range_pips=15.0)
    rows = [(1.1005, 1.0995, 1.1000)] * 6 + [(1.0994, 1.0988, 1.0990)]
    quote = Quote(symbol="EUR_USD", bid=1.0989, ask=1.0991, time=_candles(rows)[-1].time)

    signal = strat.evaluate(_candles(rows), quote)
    assert signal is not None
    assert signal.side == OrderSide.SELL


def test_skips_when_opening_range_too_wide():
    strat = EurUsdOpeningRangeBreakoutStrategy(range_candles=6, max_range_pips=15.0)
    # 40-pip opening range -> too wide, no clean expansion expected.
    rows = [(1.1020, 1.0980, 1.1000)] * 6 + [(1.1030, 1.1024, 1.1028)]
    quote = Quote(symbol="EUR_USD", bid=1.1027, ask=1.1029, time=_candles(rows)[-1].time)

    assert strat.evaluate(_candles(rows), quote) is None


def test_no_signal_inside_the_range():
    strat = EurUsdOpeningRangeBreakoutStrategy(range_candles=6, max_range_pips=15.0)
    rows = [(1.1005, 1.0995, 1.1000)] * 6 + [(1.1003, 1.0997, 1.1001)]
    quote = Quote(symbol="EUR_USD", bid=1.1000, ask=1.1002, time=_candles(rows)[-1].time)

    assert strat.evaluate(_candles(rows), quote) is None
