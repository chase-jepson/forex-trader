"""File-based emergency stop: trips block all new orders."""
from forex_trader.safety.emergency import (
    clear_emergency_stop,
    is_emergency_stopped,
    trip_emergency_stop,
)


def test_not_stopped_when_file_absent(tmp_path):
    assert is_emergency_stopped(tmp_path / "STOP") is False


def test_trip_creates_stop_and_is_detected(tmp_path):
    path = tmp_path / "STOP"
    trip_emergency_stop(path, reason="manual halt")

    assert is_emergency_stopped(path) is True
    assert "manual halt" in path.read_text()


def test_clear_removes_stop(tmp_path):
    path = tmp_path / "STOP"
    trip_emergency_stop(path, reason="halt")
    clear_emergency_stop(path)

    assert is_emergency_stopped(path) is False


def test_clear_is_idempotent_when_absent(tmp_path):
    clear_emergency_stop(tmp_path / "missing")  # must not raise
