from __future__ import annotations

from forex_trader.analysis.regime import ReversionRegimeTracker
from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import PIP_SIZE, Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class EurUsdRegimeReversionStrategy(Strategy):
    """Session-mean reversion, gated by a forecastable multi-day regime signal.

    The plain reversion edge is regime-dependent: it pays when the market has
    recently been mean-reverting and loses when it has been trending. Whether
    reversion paid over the trailing few days predicts the next day ~59-62% of
    the time, so this strategy only fades extension when the recent regime
    favors reversion. In a 12-month both-halves walk-forward this gating turned
    a losing half positive while preserving the winning half — the first rule in
    the search to survive that test.

    The strategy is stateful: it holds a ReversionRegimeTracker. The backtest /
    live loop feeds completed reversion outcomes back via
    observe_reversion_outcome so the regime read stays current. Deterministic —
    no LLM at runtime.
    """

    strategy_id = "eurusd_regime_reversion"

    def __init__(
        self,
        *,
        min_history: int = 6,
        extension_pips: float = 22.0,   # validated config (2yr 4-period walk-forward)
        target_fraction: float = 0.5,
        stop_pips: float = 12.0,
        max_spread_pips: float = 2.0,
        regime_window: int = 8,
        regime_threshold: float = 5.0,  # trade only in strongly-reverting regimes
        volume_mult: float = 1.2,        # require an elevated (exhaustion) volume
    ) -> None:
        self.min_history = min_history
        self.extension_pips = extension_pips
        self.target_fraction = target_fraction
        self.stop_pips = stop_pips
        self.max_spread_pips = max_spread_pips
        self.volume_mult = volume_mult
        self.required_history = min_history + 1
        self.regime = ReversionRegimeTracker(
            window=regime_window, favor_threshold=regime_threshold
        )

    def observe_reversion_outcome(self, pnl_pips: float) -> None:
        """Feed a completed reversion trade's pip result to the regime tracker."""
        self.regime.record_outcome(pnl_pips)

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if quote is None or len(candles) <= self.min_history:
            return None
        if quote.spread_pips > self.max_spread_pips:
            return None
        if not self.regime.reversion_favored():
            return None  # recent regime does not favor reversion — stand aside

        prior = candles[:-1]
        mean = sum(c.close for c in prior) / len(prior)
        latest_candle = candles[-1]
        latest = latest_candle.close
        deviation_pips = (latest - mean) / PIP_SIZE
        if abs(deviation_pips) < self.extension_pips:
            return None

        # Volume gate: the extension must be a high-volume exhaustion spike.
        if self.volume_mult > 0:
            avg_volume = sum(c.volume for c in prior) / len(prior)
            if avg_volume <= 0 or latest_candle.volume < avg_volume * self.volume_mult:
                return None

        stop = self.stop_pips * PIP_SIZE
        target_move = abs(latest - mean) * self.target_fraction
        if deviation_pips > 0:
            return Signal(
                strategy_id=self.strategy_id, symbol=quote.symbol, side=OrderSide.SELL,
                entry_price=latest, stop_loss=latest + stop, take_profit=latest - target_move,
                reason="Faded extension above session mean (regime favors reversion).",
                metadata={"session_mean": mean, "deviation_pips": deviation_pips},
            )
        return Signal(
            strategy_id=self.strategy_id, symbol=quote.symbol, side=OrderSide.BUY,
            entry_price=latest, stop_loss=latest - stop, take_profit=latest + target_move,
            reason="Faded extension below session mean (regime favors reversion).",
            metadata={"session_mean": mean, "deviation_pips": deviation_pips},
        )
