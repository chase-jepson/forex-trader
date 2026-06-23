from __future__ import annotations

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import PIP_SIZE, Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class EurUsdMeanReversionStrategy(Strategy):
    """Fade an overextended move back toward a short-term average.

    When the latest close sits more than `deviation_pips` away from the simple
    moving average of the last `lookback` closes, enter in the reverting
    direction with the average as the target and a stop beyond the extreme.
    """

    strategy_id = "eurusd_mean_reversion"

    def __init__(
        self,
        *,
        lookback: int = 20,
        deviation_pips: float = 12.0,
        max_spread_pips: float = 2.0,
        stop_buffer_pips: float = 6.0,
    ) -> None:
        self.lookback = lookback
        self.deviation_pips = deviation_pips
        self.max_spread_pips = max_spread_pips
        self.stop_buffer_pips = stop_buffer_pips
        # Needs `lookback` prior closes plus the latest candle.
        self.required_history = lookback + 1

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if quote is None or len(candles) <= self.lookback:
            return None
        if quote.spread_pips > self.max_spread_pips:
            return None

        window = candles[-(self.lookback + 1) : -1]
        average = sum(c.close for c in window) / len(window)
        latest = candles[-1].close
        deviation = (latest - average) / PIP_SIZE
        buffer = self.stop_buffer_pips * PIP_SIZE

        if deviation >= self.deviation_pips:
            # Extended above the average -> sell, target the average.
            return Signal(
                strategy_id=self.strategy_id,
                symbol=quote.symbol,
                side=OrderSide.SELL,
                entry_price=latest,
                stop_loss=latest + buffer,
                take_profit=average,
                reason="Price extended above the short-term average; fading back down.",
                metadata={"average": average, "deviation_pips": deviation},
            )
        if deviation <= -self.deviation_pips:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=quote.symbol,
                side=OrderSide.BUY,
                entry_price=latest,
                stop_loss=latest - buffer,
                take_profit=average,
                reason="Price extended below the short-term average; fading back up.",
                metadata={"average": average, "deviation_pips": deviation},
            )
        return None
