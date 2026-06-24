"""Regime-adaptive gate: only trade reversion when the recent regime favors it."""
from forex_trader.analysis.regime import ReversionRegimeTracker


def test_tracker_starts_neutral_and_allows_by_default():
    t = ReversionRegimeTracker(window=3)
    # With no history, default to allowing trades (innocent until proven).
    assert t.reversion_favored() is True


def test_tracker_blocks_after_recent_reversion_losses():
    t = ReversionRegimeTracker(window=3)
    t.record_outcome(-10)
    t.record_outcome(-8)
    t.record_outcome(-12)
    # Trailing window net-negative -> regime does not favor reversion -> block.
    assert t.reversion_favored() is False


def test_tracker_allows_after_recent_reversion_wins():
    t = ReversionRegimeTracker(window=3)
    t.record_outcome(15)
    t.record_outcome(-5)
    t.record_outcome(12)
    # Net positive over the window -> favored.
    assert t.reversion_favored() is True


def test_window_only_considers_recent_outcomes():
    t = ReversionRegimeTracker(window=2)
    t.record_outcome(-100)  # old big loss, should age out
    t.record_outcome(10)
    t.record_outcome(12)
    assert t.reversion_favored() is True
