from __future__ import annotations

import os
from dataclasses import dataclass


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_mode: str = os.getenv("APP_MODE", "simulated")
    trade_symbol: str = os.getenv("TRADE_SYMBOL", "EUR_USD")
    max_risk_per_trade: float = _env_float("MAX_RISK_PER_TRADE", 0.0025)
    max_daily_loss: float = _env_float("MAX_DAILY_LOSS", 0.01)
    max_open_positions: int = _env_int("MAX_OPEN_POSITIONS", 1)
    max_hold_minutes: int = _env_int("MAX_HOLD_MINUTES", 90)
    session_start_local: str = os.getenv("SESSION_START_LOCAL", "05:00")
    session_end_local: str = os.getenv("SESSION_END_LOCAL", "09:00")
    session_tz: str = os.getenv("SESSION_TZ", "America/Mexico_City")
    database_path: str = os.getenv("DATABASE_PATH", "data/forex-trader.db")
    dashboard_refresh_seconds: int = _env_int("DASHBOARD_REFRESH_SECONDS", 5)
    enable_live_trading: bool = _env_bool("ENABLE_LIVE_TRADING", False)
    emergency_stop_path: str = os.getenv("EMERGENCY_STOP_PATH", "STOP_TRADING")
    oanda_account_id: str = os.getenv("OANDA_ACCOUNT_ID", "")
    oanda_api_token: str = os.getenv("OANDA_API_TOKEN", "")
