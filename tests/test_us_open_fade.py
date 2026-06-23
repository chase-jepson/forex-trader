"""Draft US-open fade strategy: fade thrusts beyond the opening range."""
from datetime import UTC, datetime, timedelta

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote
from forex_trader.strategy.eurusd_us_open_fade import EurUsdUsOpenFadeStrategy


def _candles(closes):
    start = datetime(2026, 6, 1, 12, 30, tzinfo=UTC)
    out = []
    for i, c in enumerate(closes):
        out.append(Candle(time=start + timedelta(minutes=5 * i),
                          open=c, high=c + 0.0001, low=c - 0.0001, close=c))
    return out


def test_fades_a_thrust_above_the_opening_range():
    strat = EurUsdUsOpenFadeStrategy(range_candles=3, thrust_pips=8.0, max_spread_pips=2.0)
    # First 3 candles form the range ~1.1000; then a thrust up to 1.1015.
    candles = _candles([1.1000, 1.1002, 1.0998, 1.1015])
    quote = Quote(symbol="EUR_USD", bid=1.1014, ask=1.1016, time=candles[-1].time)

    signal = strat.evaluate(candles, quote)

    assert signal is not None
    assert signal.side == OrderSide.SELL  # fade the upside thrust
    assert signal.take_profit < signal.entry_price


def test_fades_a_thrust_below_the_opening_range():
    strat = EurUsdUsOpenFadeStrategy(range_candles=3, thrust_pips=8.0, max_spread_pips=2.0)
    candles = _candles([1.1000, 1.1002, 1.0998, 1.0985])
    quote = Quote(symbol="EUR_USD", bid=1.0984, ask=1.0986, time=candles[-1].time)

    signal = strat.evaluate(candles, quote)

    assert signal is not None
    assert signal.side == OrderSide.BUY


def test_no_signal_without_a_thrust():
    strat = EurUsdUsOpenFadeStrategy(range_candles=3, thrust_pips=8.0, max_spread_pips=2.0)
    candles = _candles([1.1000, 1.1002, 1.0998, 1.1003])  # stays in range
    quote = Quote(symbol="EUR_USD", bid=1.1002, ask=1.1004, time=candles[-1].time)

    assert strat.evaluate(candles, quote) is None


def test_draft_strategy_is_gated_in_registry():
    from forex_trader.research.registry import ResearchRegistry

    registry = ResearchRegistry.with_default_hypotheses()
    # The fade strategy must NOT be ready_for_sim until validated.
    assert registry.is_strategy_ready("eurusd_us_open_fade") is False
