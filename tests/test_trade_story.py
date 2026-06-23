"""Persist and retrieve a trade's full lifecycle story for the explorer."""
from forex_trader.storage.repositories import TradingRepository


def _candles_payload():
    return [
        {"time": "2026-06-22T11:55:00+00:00", "open": 1.1000, "high": 1.1010,
         "low": 1.0990, "close": 1.1005},
        {"time": "2026-06-22T11:56:00+00:00", "open": 1.1005, "high": 1.1020,
         "low": 1.1000, "close": 1.1015},
    ]


def test_open_and_close_trade_story_round_trips(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")

    repo.open_trade_story(
        position_id="pos-1",
        opened_at="2026-06-22T12:00:00+00:00",
        side="buy",
        entry_price=1.1016,
        stop_loss=1.0990,
        take_profit=1.1060,
        units=25000,
        signal_reason="Close broke above the opening range; spread acceptable.",
        signal_metadata={"opening_high": 1.1020, "opening_low": 1.0990},
        risk_reason="Approved: within 0.25% risk.",
        context_candles=_candles_payload(),
    )
    repo.close_trade_story(
        position_id="pos-1",
        closed_at="2026-06-22T12:45:00+00:00",
        close_price=1.1060,
        outcome="win",
        pnl=110.0,
        exit_reason="take_profit",
    )

    story = repo.get_trade_story("pos-1")

    assert story is not None
    assert story["side"] == "buy"
    assert story["entry_price"] == 1.1016
    assert story["outcome"] == "win"
    assert story["pnl"] == 110.0
    assert story["exit_reason"] == "take_profit"
    assert len(story["context_candles"]) == 2
    assert story["signal_metadata"]["opening_high"] == 1.1020


def test_list_trade_stories_returns_all_with_open_ones_marked(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")
    repo.open_trade_story(
        position_id="pos-open", opened_at="2026-06-22T12:00:00+00:00", side="buy",
        entry_price=1.10, stop_loss=1.09, take_profit=1.11, units=1000,
        signal_reason="r", signal_metadata={}, risk_reason="ok",
        context_candles=_candles_payload(),
    )

    stories = repo.list_trade_stories()

    assert len(stories) == 1
    assert stories[0]["position_id"] == "pos-open"
    assert stories[0]["outcome"] == "open"  # not yet closed


def test_get_missing_trade_story_returns_none(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")
    assert repo.get_trade_story("nope") is None


def test_clear_all_empties_trades(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")
    repo.open_trade_story(
        position_id="p", opened_at="2026-06-22T12:00:00+00:00", side="buy",
        entry_price=1.1, stop_loss=1.09, take_profit=1.11, units=1000,
        signal_reason="r", signal_metadata={}, risk_reason="ok",
        context_candles=_candles_payload(),
    )
    repo.clear_all()
    assert repo.list_trade_stories() == []
