from __future__ import annotations

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import PIP_SIZE, Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class EurUsdOpeningRangeBreakoutStrategy(Strategy):
    """Trade a clean directional expansion out of a TIGHT opening range.

    Evidence basis: in 2 years of real US-open data, breaking the first-30-min
    range pays ~2.5 pips/trade gross at a 1x-range target, and filtering to only
    TIGHT opening ranges (<=15 pips) gives a result that is net-positive AFTER
    the spread and positive in 3 of 4 independent 6-month periods — the first
    candidate to pass that consistency test. The intuition: a quiet, coiled
    opening predicts a real expansion, whereas a wide opening is already noisy.

    This is direction-via-volatility (the breakout direction), distinct from the
    rejected price-pattern reversion lines. Deterministic; no LLM at runtime.

    One trade per session (the first break of the opening range).
    """

    strategy_id = "eurusd_opening_range_breakout"

    def __init__(
        self,
        *,
        range_candles: int = 6,
        max_range_pips: float = 12.0,  # tight openings only (validated 10-15 band)
        target_mult: float = 1.0,
        stop_mult: float = 0.5,
        max_spread_pips: float = 2.0,
    ) -> None:
        self.range_candles = range_candles
        self.max_range_pips = max_range_pips
        self.target_mult = target_mult
        self.stop_mult = stop_mult
        self.max_spread_pips = max_spread_pips
        self.required_history = range_candles + 1
        # One breakout trade per session: remember the last session date traded
        # so we don't re-enter the same move repeatedly (which would compound a
        # single expansion into many leveraged re-entries).
        self._last_session_date: str | None = None

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if quote is None or len(candles) <= self.range_candles:
            return None
        if quote.spread_pips > self.max_spread_pips:
            return None

        # Only one breakout trade per session (per calendar day of the latest
        # candle). The opening range is the first `range_candles` of THIS day.
        session_date = candles[-1].time.date().isoformat()
        if session_date == self._last_session_date:
            return None
        today = [c for c in candles if c.time.date().isoformat() == session_date]
        if len(today) <= self.range_candles:
            return None

        opening = today[: self.range_candles]
        range_high = max(c.high for c in opening)
        range_low = min(c.low for c in opening)
        range_pips = (range_high - range_low) / PIP_SIZE
        if range_pips <= 0 or range_pips > self.max_range_pips:
            return None  # only trade tight, coiled openings

        latest = candles[-1].close
        target = range_pips * self.target_mult * PIP_SIZE
        stop = range_pips * self.stop_mult * PIP_SIZE

        if latest > range_high:
            self._last_session_date = session_date
            return Signal(
                strategy_id=self.strategy_id, symbol=quote.symbol, side=OrderSide.BUY,
                entry_price=range_high,
                stop_loss=range_high - stop,
                take_profit=range_high + target,
                reason="Broke above a tight opening range (expansion expected).",
                metadata={"range_high": range_high, "range_low": range_low,
                          "range_pips": range_pips},
            )
        if latest < range_low:
            self._last_session_date = session_date
            return Signal(
                strategy_id=self.strategy_id, symbol=quote.symbol, side=OrderSide.SELL,
                entry_price=range_low,
                stop_loss=range_low + stop,
                take_profit=range_low - target,
                reason="Broke below a tight opening range (expansion expected).",
                metadata={"range_high": range_high, "range_low": range_low,
                          "range_pips": range_pips},
            )
        return None
