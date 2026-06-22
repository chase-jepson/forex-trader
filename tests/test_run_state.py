"""Run-state persistence so a restarted loop resumes daily PnL and day boundary."""
from forex_trader.storage.repositories import TradingRepository


def test_run_state_round_trips(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")

    repo.save_run_state(
        last_tick="2026-06-22T12:00:00+00:00",
        current_day="2026-06-22",
        daily_realized_pnl=-12.5,
        cumulative_realized_pnl=33.0,
    )
    state = repo.load_run_state()

    assert state is not None
    assert state["current_day"] == "2026-06-22"
    assert state["daily_realized_pnl"] == -12.5
    assert state["cumulative_realized_pnl"] == 33.0


def test_load_run_state_is_none_when_empty(tmp_path):
    repo = TradingRepository(tmp_path / "empty.db")
    assert repo.load_run_state() is None


def test_save_run_state_overwrites_previous(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")
    repo.save_run_state(last_tick="t1", current_day="2026-06-22",
                        daily_realized_pnl=1.0, cumulative_realized_pnl=1.0)
    repo.save_run_state(last_tick="t2", current_day="2026-06-23",
                        daily_realized_pnl=0.0, cumulative_realized_pnl=5.0)

    state = repo.load_run_state()
    assert state["current_day"] == "2026-06-23"
    assert state["cumulative_realized_pnl"] == 5.0
