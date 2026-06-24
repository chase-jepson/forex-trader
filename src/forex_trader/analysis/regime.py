from __future__ import annotations

from collections import deque


class ReversionRegimeTracker:
    """Tracks whether the recent regime has favored reversion trades.

    Evidence basis: whether reversion paid over the trailing few days predicts
    whether it pays the next day ~59-62% of the time (vs ~47% for price
    direction). So we keep a rolling record of recent reversion outcomes and
    only allow new reversion trades when the trailing window is net-positive.

    Deterministic and tiny (one parameter, the window) to resist overfitting.
    """

    def __init__(self, *, window: int = 5) -> None:
        self.window = window
        self._outcomes: deque[float] = deque(maxlen=window)

    def record_outcome(self, pnl_pips: float) -> None:
        """Record the realized pip result of a completed reversion trade."""
        self._outcomes.append(pnl_pips)

    def reversion_favored(self) -> bool:
        """True when the recent regime favors reversion (or there is no history
        yet — innocent until proven otherwise)."""
        if not self._outcomes:
            return True
        return sum(self._outcomes) > 0
