from __future__ import annotations

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import PIP_SIZE, Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class EurUsdUsOpenFadeStrategy(Strategy):
    """DRAFT: fade a thrust beyond the opening range during the US open.

    Evidence basis: in 6 months of real US-open data, breakouts continued only
    ~47% of the time — i.e. the window mean-reverts after a thrust. This strategy
    fades that thrust (sell a push above the opening range, buy a push below),
    targeting the range mid with a stop beyond the extreme.

    It is intentionally NOT registered as ready_for_sim — it must be backtested
    and walk-forward validated before it can run. The selector keeps it behind
    NullStrategy until the research registry marks it ready.
    """

    strategy_id = "eurusd_us_open_fade"

    def __init__(
        self,
        *,
        range_candles: int = 6,
        thrust_pips: float = 8.0,
        max_spread_pips: float = 2.0,
        stop_buffer_pips: float = 4.0,
    ) -> None:
        self.range_candles = range_candles
        self.thrust_pips = thrust_pips
        self.max_spread_pips = max_spread_pips
        self.stop_buffer_pips = stop_buffer_pips
        self.required_history = range_candles + 1

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if quote is None or len(candles) <= self.range_candles:
            return None
        if quote.spread_pips > self.max_spread_pips:
            return None

        opening = candles[: self.range_candles]
        range_high = max(c.high for c in opening)
        range_low = min(c.low for c in opening)
        range_mid = (range_high + range_low) / 2
        latest = candles[-1].close
        buffer = self.stop_buffer_pips * PIP_SIZE
        thrust = self.thrust_pips * PIP_SIZE

        if latest >= range_high + thrust:
            # Thrust above the range -> fade short, target the mid.
            return Signal(
                strategy_id=self.strategy_id,
                symbol=quote.symbol,
                side=OrderSide.SELL,
                entry_price=latest,
                stop_loss=latest + buffer,
                take_profit=range_mid,
                reason="Faded a thrust above the opening range (US open mean-reverts).",
                metadata={"range_high": range_high, "range_low": range_low,
                          "range_mid": range_mid},
            )
        if latest <= range_low - thrust:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=quote.symbol,
                side=OrderSide.BUY,
                entry_price=latest,
                stop_loss=latest - buffer,
                take_profit=range_mid,
                reason="Faded a thrust below the opening range (US open mean-reverts).",
                metadata={"range_high": range_high, "range_low": range_low,
                          "range_mid": range_mid},
            )
        return None
