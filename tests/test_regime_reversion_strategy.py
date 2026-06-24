"""Production regime-gated reversion strategy: stateful regime gate."""
from datetime import UTC, datetime, timedelta

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote
from forex_trader.strategy.eurusd_regime_reversion import EurUsdRegimeReversionStrategy


def _candles(rows):
    start = datetime(2026, 6, 1, 12, 30, tzinfo=UTC)
    return [Candle(time=start + timedelta(minutes=5 * i), open=c, high=c + 0.0001,
                   low=c - 0.0001, close=c, volume=1000) for i, c in enumerate(rows)]


def test_emits_reversion_signal_when_extended_and_regime_neutral():
    # Fresh tracker defaults to favored -> a deep extension produces a fade.
    strat = EurUsdRegimeReversionStrategy(min_history=6, extension_pips=18.0)
    rows = [1.1000] * 6 + [1.1020]
    quote = Quote(symbol="EUR_USD", bid=1.1019, ask=1.1021, time=_candles(rows)[-1].time)

    signal = strat.evaluate(_candles(rows), quote)
    assert signal is not None
    assert signal.side == OrderSide.SELL


def test_blocks_when_regime_unfavorable():
    strat = EurUsdRegimeReversionStrategy(min_history=6, extension_pips=18.0, regime_window=3)
    # Feed the tracker recent reversion losses -> regime turns unfavorable.
    strat.observe_reversion_outcome(-15)
    strat.observe_reversion_outcome(-12)
    strat.observe_reversion_outcome(-10)

    rows = [1.1000] * 6 + [1.1020]
    quote = Quote(symbol="EUR_USD", bid=1.1019, ask=1.1021, time=_candles(rows)[-1].time)

    assert strat.evaluate(_candles(rows), quote) is None


def test_no_signal_when_not_extended():
    strat = EurUsdRegimeReversionStrategy(min_history=6, extension_pips=18.0)
    rows = [1.1000] * 6 + [1.1003]
    quote = Quote(symbol="EUR_USD", bid=1.1002, ask=1.1004, time=_candles(rows)[-1].time)
    assert strat.evaluate(_candles(rows), quote) is None
