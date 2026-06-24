"""The regime strategy must observe extension outcomes itself, even when not
trading, so the regime read stays live and doesn't deadlock."""
from datetime import UTC, datetime, timedelta

from forex_trader.domain.models import Candle, Quote
from forex_trader.strategy.eurusd_regime_reversion import EurUsdRegimeReversionStrategy


def _series(closes, vols=None):
    start = datetime(2026, 6, 1, 12, 30, tzinfo=UTC)
    vols = vols or [2000] * len(closes)
    return [Candle(time=start + timedelta(minutes=5 * i), open=c, high=c + 0.0002,
                   low=c - 0.0002, close=c, volume=vols[i]) for i, c in enumerate(closes)]


def test_regime_strength_updates_from_observed_extensions_without_trading():
    # Force the gate shut so it can't trade, then feed candles where extensions
    # clearly reverted; the strategy should still observe and update its regime.
    strat = EurUsdRegimeReversionStrategy(min_history=6, extension_pips=18.0,
                                          regime_window=10)
    # Build a series: mean ~1.1000, repeated extension-then-revert patterns.
    closes = [1.1000] * 6
    for _ in range(3):
        closes += [1.1020, 1.1000]  # extend +20p then revert to mean
    quote_time = _series(closes)[-1].time
    q = Quote(symbol="EUR_USD", bid=1.0999, ask=1.1001, time=quote_time)

    # Drive the strategy candle-by-candle as the runner would.
    series = _series(closes)
    for i in range(7, len(series) + 1):
        strat.evaluate(series[:i], q)

    # Having observed reverting extensions, the regime strength should be > 0.
    assert strat.regime.strength() > 0


def test_observed_outcomes_recover_after_a_bad_start():
    # A bad early extension (didn't revert) then good ones -> regime recovers,
    # not permanently deadlocked.
    strat = EurUsdRegimeReversionStrategy(min_history=6, extension_pips=18.0,
                                          regime_window=4)
    closes = [1.1000] * 6 + [1.1020, 1.1040]  # extend up then keep going (no revert)
    for _ in range(4):
        closes += [1.1020, 1.1000]            # then several clean reverts
    series = _series(closes)
    q = Quote(symbol="EUR_USD", bid=1.0999, ask=1.1001, time=series[-1].time)
    for i in range(7, len(series) + 1):
        strat.evaluate(series[:i], q)

    assert strat.regime.strength() > 0  # recovered, not stuck negative
