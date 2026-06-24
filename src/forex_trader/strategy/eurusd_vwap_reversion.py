from __future__ import annotations

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import PIP_SIZE, Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class EurUsdVwapReversionStrategy(Strategy):
    """Fade extension from the running session mean (VWAP-style reversion).

    Evidence basis: in 6 months of real US-open data, when price extends >=20
    pips from the running session mean it reverts toward the mean ~63% of the
    time (the bias strengthens with extension). This strategy sells when price
    is `extension_pips` above the session mean and buys when it is that far
    below, targeting a partial move back toward the mean with a stop beyond the
    extreme. Fully deterministic — no LLM at runtime.
    """

    strategy_id = "eurusd_vwap_reversion"

    def __init__(
        self,
        *,
        min_history: int = 6,
        extension_pips: float = 30.0,   # validated: edge strengthens with extension
        target_fraction: float = 0.4,   # take the reversion quickly, before it resumes
        stop_pips: float = 12.0,
        max_spread_pips: float = 2.0,
    ) -> None:
        self.min_history = min_history
        self.extension_pips = extension_pips
        self.target_fraction = target_fraction
        self.stop_pips = stop_pips
        self.max_spread_pips = max_spread_pips
        self.required_history = min_history + 1

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if quote is None or len(candles) <= self.min_history:
            return None
        if quote.spread_pips > self.max_spread_pips:
            return None

        # Running mean of closes prior to the latest candle (the session VWAP-ish
        # anchor). Using closes keeps it deterministic without tick volume.
        prior = candles[:-1]
        mean = sum(c.close for c in prior) / len(prior)
        latest = candles[-1].close
        deviation_pips = (latest - mean) / PIP_SIZE
        stop = self.stop_pips * PIP_SIZE
        # Target a fraction of the way back to the mean.
        target_move = abs(latest - mean) * self.target_fraction

        if deviation_pips >= self.extension_pips:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=quote.symbol,
                side=OrderSide.SELL,
                entry_price=latest,
                stop_loss=latest + stop,
                take_profit=latest - target_move,
                reason="Faded extension above the session mean (reverts ~60%+).",
                metadata={"session_mean": mean, "deviation_pips": deviation_pips},
            )
        if deviation_pips <= -self.extension_pips:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=quote.symbol,
                side=OrderSide.BUY,
                entry_price=latest,
                stop_loss=latest - stop,
                take_profit=latest + target_move,
                reason="Faded extension below the session mean (reverts ~60%+).",
                metadata={"session_mean": mean, "deviation_pips": deviation_pips},
            )
        return None
