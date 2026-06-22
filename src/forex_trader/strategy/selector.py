from __future__ import annotations

from forex_trader.research.registry import ResearchRegistry
from forex_trader.strategy.base import Strategy
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy
from forex_trader.strategy.null_strategy import NullStrategy


def select_strategy(registry: ResearchRegistry, strategy_id: str) -> Strategy:
    if not registry.is_strategy_ready(strategy_id):
        return NullStrategy()
    if strategy_id == "eurusd_opening_window":
        return EurUsdOpeningWindowStrategy()
    return NullStrategy()

