"""Volume-confirmed session-mean reversion: fade exhaustion spikes."""
from datetime import UTC, datetime, timedelta

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote
from forex_trader.strategy.eurusd_volume_reversion import EurUsdVolumeReversionStrategy


def _candles(rows):
    # rows: list of (close, volume)
    start = datetime(2026, 6, 1, 12, 30, tzinfo=UTC)
    return [Candle(time=start + timedelta(minutes=5 * i), open=c, high=c + 0.0001,
                   low=c - 0.0001, close=c, volume=v) for i, (c, v) in enumerate(rows)]


def test_fades_high_volume_spike_above_mean():
    strat = EurUsdVolumeReversionStrategy(min_history=6, extension_pips=18.0,
                                          volume_mult=1.3, max_spread_pips=2.0)
    # Quiet mean ~1.1000 at vol 800; then a high-vol spike 20p above.
    rows = [(1.1000, 800)] * 6 + [(1.1020, 1500)]
    quote = Quote(symbol="EUR_USD", bid=1.1019, ask=1.1021, time=_candles(rows)[-1].time)

    signal = strat.evaluate(_candles(rows), quote)

    assert signal is not None
    assert signal.side == OrderSide.SELL


def test_no_signal_when_extension_but_low_volume():
    strat = EurUsdVolumeReversionStrategy(min_history=6, extension_pips=18.0,
                                          volume_mult=1.3, max_spread_pips=2.0)
    # Same extension but the spike is LOW volume -> no exhaustion -> skip.
    rows = [(1.1000, 800)] * 6 + [(1.1020, 600)]
    quote = Quote(symbol="EUR_USD", bid=1.1019, ask=1.1021, time=_candles(rows)[-1].time)

    assert strat.evaluate(_candles(rows), quote) is None


def test_no_signal_when_near_mean_even_with_high_volume():
    strat = EurUsdVolumeReversionStrategy(min_history=6, extension_pips=18.0,
                                          volume_mult=1.3, max_spread_pips=2.0)
    rows = [(1.1000, 800)] * 6 + [(1.1003, 2000)]  # high vol but only 3p from mean
    quote = Quote(symbol="EUR_USD", bid=1.1002, ask=1.1004, time=_candles(rows)[-1].time)

    assert strat.evaluate(_candles(rows), quote) is None
