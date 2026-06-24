from __future__ import annotations

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import PIP_SIZE, Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class EurUsdVolumeReversionStrategy(Strategy):
    """Fade an extension from the session mean ONLY when volume confirms exhaustion.

    Evidence basis (6mo real US-open data): price extended >=20 pips from the
    running session mean reverts ~63% of the time, and ~69% when that extension
    happens on a high-volume candle (a climax/exhaustion spike). This strategy
    adds the volume gate on top of the mean-reversion entry — a genuinely
    different signal than price alone. Deterministic; no LLM at runtime.

    NOTE: must still pass the 12-month both-halves walk-forward before it is
    trusted — prior price-only reversion looked good on 6mo and failed on 12mo.
    """

    strategy_id = "eurusd_volume_reversion"

    def __init__(
        self,
        *,
        min_history: int = 6,
        extension_pips: float = 20.0,
        volume_mult: float = 1.3,
        target_fraction: float = 0.4,
        stop_pips: float = 12.0,
        max_spread_pips: float = 2.0,
    ) -> None:
        self.min_history = min_history
        self.extension_pips = extension_pips
        self.volume_mult = volume_mult
        self.target_fraction = target_fraction
        self.stop_pips = stop_pips
        self.max_spread_pips = max_spread_pips
        self.required_history = min_history + 1

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if quote is None or len(candles) <= self.min_history:
            return None
        if quote.spread_pips > self.max_spread_pips:
            return None

        prior = candles[:-1]
        mean = sum(c.close for c in prior) / len(prior)
        latest = candles[-1]
        deviation_pips = (latest.close - mean) / PIP_SIZE

        if abs(deviation_pips) < self.extension_pips:
            return None

        # Volume gate: the extension candle must be a high-volume (exhaustion)
        # spike relative to the session's average volume so far.
        avg_volume = sum(c.volume for c in prior) / len(prior)
        if avg_volume <= 0 or latest.volume < avg_volume * self.volume_mult:
            return None

        stop = self.stop_pips * PIP_SIZE
        target_move = abs(latest.close - mean) * self.target_fraction

        if deviation_pips > 0:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=quote.symbol,
                side=OrderSide.SELL,
                entry_price=latest.close,
                stop_loss=latest.close + stop,
                take_profit=latest.close - target_move,
                reason="Faded a high-volume exhaustion spike above the session mean.",
                metadata={"session_mean": mean, "deviation_pips": deviation_pips,
                          "volume": latest.volume, "avg_volume": round(avg_volume, 1)},
            )
        return Signal(
            strategy_id=self.strategy_id,
            symbol=quote.symbol,
            side=OrderSide.BUY,
            entry_price=latest.close,
            stop_loss=latest.close - stop,
            take_profit=latest.close + target_move,
            reason="Faded a high-volume exhaustion spike below the session mean.",
            metadata={"session_mean": mean, "deviation_pips": deviation_pips,
                      "volume": latest.volume, "avg_volume": round(avg_volume, 1)},
        )
