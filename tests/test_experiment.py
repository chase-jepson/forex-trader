"""Offline experiment harness: load cached candles, walk-forward a strategy."""
from forex_trader.analysis.experiment import (
    load_cached_candles,
    risk_adjusted_score,
    walk_forward_strategy,
)
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy


def test_risk_adjusted_score_rewards_profit_per_drawdown():
    # Same PnL, smaller drawdown -> higher score.
    a = risk_adjusted_score(pnl=100, max_drawdown=50, trades=20)
    b = risk_adjusted_score(pnl=100, max_drawdown=200, trades=20)
    assert a > b


def test_risk_adjusted_score_penalizes_too_few_trades():
    many = risk_adjusted_score(pnl=100, max_drawdown=50, trades=50)
    few = risk_adjusted_score(pnl=100, max_drawdown=50, trades=2)
    assert many > few  # not enough trades -> discounted


def test_walk_forward_strategy_returns_in_and_out(tmp_path):
    candles = load_cached_candles("data/history/eurusd-usopen-6mo.json")
    assert len(candles) > 1000  # cached real data present

    res = walk_forward_strategy(
        EurUsdOpeningWindowStrategy(max_spread_pips=2.0),
        candles=candles,
        session_start_local="08:30", session_end_local="11:30",
        session_tz="America/New_York",
    )
    assert "in_sample" in res and "out_of_sample" in res
    assert "pnl" in res["out_of_sample"]
