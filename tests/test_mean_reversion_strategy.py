"""Mean-reversion strategy: fade an overextended move toward a short SMA."""
from datetime import UTC, datetime, timedelta

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote
from forex_trader.strategy.eurusd_mean_reversion import EurUsdMeanReversionStrategy


def _candles(closes):
    start = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    out = []
    for i, c in enumerate(closes):
        out.append(Candle(time=start + timedelta(minutes=i), open=c, high=c + 0.0005,
                          low=c - 0.0005, close=c))
    return out


def test_sells_when_price_extends_far_above_average():
    strat = EurUsdMeanReversionStrategy(lookback=5, deviation_pips=10.0, max_spread_pips=2.0)
    # Flat ~1.1000 average, then a spike up to 1.1020 (20 pips above).
    candles = _candles([1.1000, 1.1000, 1.1000, 1.1000, 1.1000, 1.1020])
    quote = Quote(symbol="EUR_USD", bid=1.1019, ask=1.1021, time=candles[-1].time)

    signal = strat.evaluate(candles, quote)

    assert signal is not None
    assert signal.side == OrderSide.SELL
    assert signal.take_profit < signal.entry_price  # reverting down


def test_buys_when_price_extends_far_below_average():
    strat = EurUsdMeanReversionStrategy(lookback=5, deviation_pips=10.0, max_spread_pips=2.0)
    candles = _candles([1.1000, 1.1000, 1.1000, 1.1000, 1.1000, 1.0980])
    quote = Quote(symbol="EUR_USD", bid=1.0979, ask=1.0981, time=candles[-1].time)

    signal = strat.evaluate(candles, quote)

    assert signal is not None
    assert signal.side == OrderSide.BUY
    assert signal.take_profit > signal.entry_price


def test_no_signal_when_price_is_near_average():
    strat = EurUsdMeanReversionStrategy(lookback=5, deviation_pips=10.0, max_spread_pips=2.0)
    candles = _candles([1.1000, 1.1001, 1.0999, 1.1000, 1.1001, 1.1002])
    quote = Quote(symbol="EUR_USD", bid=1.1001, ask=1.1003, time=candles[-1].time)

    assert strat.evaluate(candles, quote) is None


def test_no_signal_when_spread_too_wide():
    strat = EurUsdMeanReversionStrategy(lookback=5, deviation_pips=10.0, max_spread_pips=2.0)
    candles = _candles([1.1000, 1.1000, 1.1000, 1.1000, 1.1000, 1.1020])
    quote = Quote(symbol="EUR_USD", bid=1.1010, ask=1.1030, time=candles[-1].time)  # 20-pip spread

    assert strat.evaluate(candles, quote) is None
