from __future__ import annotations

from forex_trader.domain.enums import OrderSide
from forex_trader.domain.models import Candle, Quote, Signal
from forex_trader.strategy.base import Strategy


class EurUsdOpeningWindowStrategy(Strategy):
    strategy_id = "eurusd_opening_window"

    def __init__(self, *, max_spread_pips: float = 2.0, reward_to_risk: float = 2.0) -> None:
        self.max_spread_pips = max_spread_pips
        self.reward_to_risk = reward_to_risk

    def evaluate(self, candles: list[Candle], quote: Quote | None) -> Signal | None:
        if quote is None or len(candles) < 2:
            return None
        if quote.spread_pips > self.max_spread_pips:
            return None
        opening = candles[0]
        latest = candles[-1]
        if latest.close > opening.high:
            risk = latest.close - opening.low
            return Signal(
                strategy_id=self.strategy_id,
                symbol=quote.symbol,
                side=OrderSide.BUY,
                entry_price=latest.close,
                stop_loss=opening.low,
                take_profit=latest.close + (risk * self.reward_to_risk),
                reason=(
                    "Close broke above the documented opening range "
                    "while spread was acceptable."
                ),
                metadata={"opening_high": opening.high, "opening_low": opening.low},
            )
        if latest.close < opening.low:
            risk = opening.high - latest.close
            return Signal(
                strategy_id=self.strategy_id,
                symbol=quote.symbol,
                side=OrderSide.SELL,
                entry_price=latest.close,
                stop_loss=opening.high,
                take_profit=latest.close - (risk * self.reward_to_risk),
                reason=(
                    "Close broke below the documented opening range "
                    "while spread was acceptable."
                ),
                metadata={"opening_high": opening.high, "opening_low": opening.low},
            )
        return None
