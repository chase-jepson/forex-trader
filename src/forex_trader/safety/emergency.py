from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def is_emergency_stopped(path: str | Path) -> bool:
    """True when the emergency-stop file exists. The live loop checks this
    every tick before placing any order."""
    return Path(path).exists()


def trip_emergency_stop(path: str | Path, *, reason: str = "") -> None:
    """Create the emergency-stop file, halting new orders on the next check."""
    target = Path(path)
    if target.parent != Path("."):
        target.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).isoformat()
    target.write_text(f"EMERGENCY STOP\ntime: {stamp}\nreason: {reason}\n")


def clear_emergency_stop(path: str | Path) -> None:
    """Remove the emergency-stop file if present. Idempotent."""
    Path(path).unlink(missing_ok=True)
