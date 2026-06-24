"""Session-mean (VWAP-style) reversion: fade extension from the running mean."""
from datetime import UTC, datetime, timedelta

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote
from forex_trader.strategy.eurusd_vwap_reversion import EurUsdVwapReversionStrategy


def _candles(closes):
    start = datetime(2026, 6, 1, 12, 30, tzinfo=UTC)
    return [Candle(time=start + timedelta(minutes=5 * i), open=c, high=c + 0.0001,
                   low=c - 0.0001, close=c) for i, c in enumerate(closes)]


def test_fades_short_when_far_above_session_mean():
    strat = EurUsdVwapReversionStrategy(min_history=6, extension_pips=15.0, max_spread_pips=2.0)
    # Mean ~1.1000, last close pushed 20 pips above.
    closes = [1.1000] * 6 + [1.1020]
    quote = Quote(symbol="EUR_USD", bid=1.1019, ask=1.1021, time=_candles(closes)[-1].time)

    signal = strat.evaluate(_candles(closes), quote)

    assert signal is not None
    assert signal.side == OrderSide.SELL
    assert signal.take_profit < signal.entry_price   # target back toward mean
    assert signal.take_profit >= 1.1000 - 0.0005     # near the mean


def test_fades_long_when_far_below_session_mean():
    strat = EurUsdVwapReversionStrategy(min_history=6, extension_pips=15.0, max_spread_pips=2.0)
    closes = [1.1000] * 6 + [1.0980]
    quote = Quote(symbol="EUR_USD", bid=1.0979, ask=1.0981, time=_candles(closes)[-1].time)

    signal = strat.evaluate(_candles(closes), quote)

    assert signal is not None
    assert signal.side == OrderSide.BUY


def test_no_signal_when_near_mean():
    strat = EurUsdVwapReversionStrategy(min_history=6, extension_pips=15.0, max_spread_pips=2.0)
    closes = [1.1000] * 6 + [1.1003]  # only 3 pips from mean
    quote = Quote(symbol="EUR_USD", bid=1.1002, ask=1.1004, time=_candles(closes)[-1].time)

    assert strat.evaluate(_candles(closes), quote) is None


def test_no_signal_before_min_history():
    strat = EurUsdVwapReversionStrategy(min_history=6, extension_pips=15.0, max_spread_pips=2.0)
    closes = [1.1000, 1.1020]  # not enough history for a stable mean
    quote = Quote(symbol="EUR_USD", bid=1.1019, ask=1.1021, time=_candles(closes)[-1].time)

    assert strat.evaluate(_candles(closes), quote) is None
