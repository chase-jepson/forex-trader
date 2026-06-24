"""Regime tracker exposes a strength score and a threshold gate."""
from forex_trader.analysis.regime import ReversionRegimeTracker


def test_strength_is_sum_of_recent_outcomes():
    t = ReversionRegimeTracker(window=5)
    t.record_outcome(10)
    t.record_outcome(-3)
    t.record_outcome(8)
    assert t.strength() == 15


def test_no_history_strength_is_zero():
    assert ReversionRegimeTracker(window=5).strength() == 0.0


def test_favored_with_threshold_requires_strong_regime():
    t = ReversionRegimeTracker(window=5, favor_threshold=10.0)
    t.record_outcome(5)   # strength 5, below threshold
    assert t.reversion_favored() is False
    t.record_outcome(8)   # strength 13, above threshold
    assert t.reversion_favored() is True


def test_default_threshold_zero_keeps_old_behavior():
    t = ReversionRegimeTracker(window=3)  # default threshold 0
    t.record_outcome(1)
    assert t.reversion_favored() is True
    t2 = ReversionRegimeTracker(window=3)
    t2.record_outcome(-1)
    assert t2.reversion_favored() is False
