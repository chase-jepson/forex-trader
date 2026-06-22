from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forex_trader.config import Settings


@dataclass(frozen=True)
class StartupStatus:
    ok: bool
    reason: str


def validate_startup(
    settings: Settings,
    *,
    simulation_complete: bool = False,
    practice_complete: bool = False,
) -> StartupStatus:
    if Path(settings.emergency_stop_path).exists():
        return StartupStatus(False, "Emergency stop is active.")
    if settings.app_mode == "practice" and (
        not settings.oanda_account_id or not settings.oanda_api_token
    ):
        return StartupStatus(False, "Practice mode requires OANDA credentials.")
    if settings.app_mode == "live":
        if not settings.enable_live_trading:
            return StartupStatus(False, "Live mode must be explicitly enabled.")
        if not simulation_complete or not practice_complete:
            return StartupStatus(
                False,
                "Live mode requires completed simulation and practice gates.",
            )
    return StartupStatus(True, f"Startup checks passed for {settings.app_mode} mode.")
