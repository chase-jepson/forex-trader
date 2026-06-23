from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: str | Path = ".env") -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ.

    Existing environment variables are never overridden, so a real shell
    export always wins over the file. Missing files are ignored. No external
    dependency is required.
    """
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Config error: {name}={value!r} is not a valid number.") from None


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Config error: {name}={value!r} is not a valid integer.") from None


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_mode: str = "simulated"
    trade_symbol: str = "EUR_USD"
    max_risk_per_trade: float = 0.0025
    max_daily_loss: float = 0.10  # 10% daily-loss cap; set 0 to disable
    max_open_positions: int = 1
    max_hold_minutes: int = 90
    session_start_local: str = "05:00"
    session_end_local: str = "09:00"
    session_tz: str = "America/Mexico_City"
    database_path: str = "data/forex-trader.db"
    dashboard_refresh_seconds: int = 5
    enable_live_trading: bool = False
    emergency_stop_path: str = "STOP_TRADING"
    oanda_account_id: str = ""
    oanda_api_token: str = ""

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> Settings:
        """Build settings from the environment, loading a .env file first.

        Bare ``Settings()`` always yields the safe hardcoded defaults above so
        tests are deterministic. ``Settings.from_env()`` is the production path
        that reads ``.env`` and process environment variables.
        """
        if env_file is not None:
            load_env_file(env_file)
        return cls(
            app_mode=os.getenv("APP_MODE", cls.app_mode),
            trade_symbol=os.getenv("TRADE_SYMBOL", cls.trade_symbol),
            max_risk_per_trade=_env_float("MAX_RISK_PER_TRADE", cls.max_risk_per_trade),
            max_daily_loss=_env_float("MAX_DAILY_LOSS", cls.max_daily_loss),
            max_open_positions=_env_int("MAX_OPEN_POSITIONS", cls.max_open_positions),
            max_hold_minutes=_env_int("MAX_HOLD_MINUTES", cls.max_hold_minutes),
            session_start_local=os.getenv("SESSION_START_LOCAL", cls.session_start_local),
            session_end_local=os.getenv("SESSION_END_LOCAL", cls.session_end_local),
            session_tz=os.getenv("SESSION_TZ", cls.session_tz),
            database_path=os.getenv("DATABASE_PATH", cls.database_path),
            dashboard_refresh_seconds=_env_int(
                "DASHBOARD_REFRESH_SECONDS", cls.dashboard_refresh_seconds
            ),
            enable_live_trading=_env_bool("ENABLE_LIVE_TRADING", cls.enable_live_trading),
            emergency_stop_path=os.getenv("EMERGENCY_STOP_PATH", cls.emergency_stop_path),
            oanda_account_id=os.getenv("OANDA_ACCOUNT_ID", cls.oanda_account_id),
            oanda_api_token=os.getenv("OANDA_API_TOKEN", cls.oanda_api_token),
        )
