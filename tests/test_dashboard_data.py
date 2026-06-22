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
