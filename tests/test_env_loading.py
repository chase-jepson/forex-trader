"""Settings.from_env should load values from a .env file when present."""
from forex_trader.config import Settings, load_env_file


def test_from_env_populates_settings_from_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("APP_MODE=practice\nMAX_RISK_PER_TRADE=0.001\n")
    monkeypatch.delenv("APP_MODE", raising=False)
    monkeypatch.delenv("MAX_RISK_PER_TRADE", raising=False)

    settings = Settings.from_env(env)

    assert settings.app_mode == "practice"
    assert settings.max_risk_per_trade == 0.001


def test_load_env_file_does_not_override_existing_env(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("APP_MODE=practice\n")
    monkeypatch.setenv("APP_MODE", "simulated")

    load_env_file(env)

    # Real environment wins over the file.
    assert Settings.from_env(env_file=None).app_mode == "simulated"


def test_load_env_file_ignores_missing_file(tmp_path):
    load_env_file(tmp_path / "nope.env")  # must not raise


def test_bare_settings_uses_safe_defaults(monkeypatch):
    monkeypatch.setenv("APP_MODE", "live")
    # Bare Settings() ignores the environment for deterministic tests.
    assert Settings().app_mode == "simulated"
