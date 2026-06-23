"""Dashboard snapshot should read persisted cycles and reviews from the DB."""
from forex_trader.dashboard.app import load_dashboard_snapshot
from forex_trader.storage.repositories import TradingRepository


def test_load_snapshot_reads_persisted_reviews(tmp_path):
    repo = TradingRepository(tmp_path / "t.db")
    repo.save_cycle("c1", "2026-06-22T12:00:00", "ordered", "fired", {"k": "v"})
    repo.save_review(
        review_id="r1", trade_id="c1", outcome="win",
        payload={"outcome": "win", "pnl": 12.5, "mistake_tags": [], "summary": "ok"},
    )

    snapshot = load_dashboard_snapshot(repository=repo)

    assert snapshot["live_market"]["latest_status"] == "ordered"
    assert len(snapshot["reviews"]) == 1
    assert snapshot["reviews"][0]["outcome"] == "win"
    assert snapshot["reports"]["realized_pnl"] == 12.5


def test_load_snapshot_handles_empty_database(tmp_path):
    repo = TradingRepository(tmp_path / "empty.db")

    snapshot = load_dashboard_snapshot(repository=repo)

    assert snapshot["reviews"] == []
    assert snapshot["live_market"]["latest_status"] == "idle"


def test_snapshot_includes_persisted_trades(tmp_path):
    from forex_trader.dashboard.app import load_dashboard_snapshot

    repo = TradingRepository(tmp_path / "t.db")
    repo.open_trade_story(
        position_id="pos-1", opened_at="2026-06-22T12:00:00+00:00", side="buy",
        entry_price=1.1016, stop_loss=1.0990, take_profit=1.1060, units=25000,
        signal_reason="broke out", signal_metadata={}, risk_reason="ok",
        context_candles=[{"time": "2026-06-22T11:55:00+00:00", "open": 1.1,
                          "high": 1.101, "low": 1.099, "close": 1.1005}],
    )

    snapshot = load_dashboard_snapshot(repository=repo)

    assert len(snapshot["trades"]) == 1
    assert snapshot["trades"][0]["position_id"] == "pos-1"


def test_render_trade_explorer_handles_empty(tmp_path):
    from forex_trader.dashboard.app import build_dashboard_snapshot, render_trade_explorer

    class _FakeSt:
        def subheader(self, *a, **k): pass
        def info(self, *a, **k): self.info_called = True

    st = _FakeSt()
    snapshot = build_dashboard_snapshot(quote=None, cycles=[], reviews=[], trades=[])
    render_trade_explorer(st, snapshot)

    assert getattr(st, "info_called", False) is True
