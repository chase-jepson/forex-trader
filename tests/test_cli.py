"""CLI entry point for running backtests and reporting status."""

from forex_trader.cli import build_parser, run_backtest_command


def test_parser_supports_backtest_subcommand():
    parser = build_parser()
    args = parser.parse_args(["backtest", "--count", "100", "--seed", "5"])
    assert args.command == "backtest"
    assert args.count == 100
    assert args.seed == 5


def test_run_backtest_command_returns_summary_text(capsys):
    code = run_backtest_command(
        count=200, seed=7, strategy="opening_window",
        session_start="00:00", session_end="23:59", session_tz="UTC",
        start="2026-06-22T05:00:00+00:00",
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "final equity" in out.lower()
    assert "trades" in out.lower()


def test_run_backtest_command_rejects_unknown_strategy(capsys):
    code = run_backtest_command(
        count=50, seed=1, strategy="does_not_exist",
        session_start="00:00", session_end="23:59", session_tz="UTC",
        start="2026-06-22T05:00:00+00:00",
    )
    assert code != 0
    assert "unknown strategy" in capsys.readouterr().err.lower()


def test_parser_supports_evidence_subcommand():
    from forex_trader.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["evidence", "--days", "5", "--seed", "3"])
    assert args.command == "evidence"
    assert args.days == 5
    assert args.seed == 3


def test_run_evidence_command_writes_report(tmp_path, capsys):
    from forex_trader.cli import run_evidence_command

    out_path = tmp_path / "evidence.md"
    code = run_evidence_command(days=2, seed=7, out_path=str(out_path))

    assert code == 0
    text = out_path.read_text()
    # Report names each strategy and a verdict line.
    assert "opening_window" in text
    assert "mean_reversion" in text
    assert "verdict" in text.lower()
    # And the comparison table prints to stdout.
    assert "strategy" in capsys.readouterr().out.lower()


def test_live_command_refuses_in_simulated_mode(capsys):
    from forex_trader.cli import run_live_command

    code = run_live_command(
        arm=False, acknowledge=True, max_iterations=1,
        app_mode="simulated", account_id="x", token="y", enable_live=False,
    )
    assert code != 0
    assert "practice" in capsys.readouterr().err.lower()


def test_live_command_refuses_without_acknowledgement(capsys):
    from forex_trader.cli import run_live_command

    code = run_live_command(
        arm=True, acknowledge=False, max_iterations=1,
        app_mode="practice", account_id="x", token="y", enable_live=False,
    )
    assert code != 0
    assert "acknowledge" in capsys.readouterr().err.lower()


def test_live_command_refuses_without_credentials(capsys):
    from forex_trader.cli import run_live_command

    code = run_live_command(
        arm=False, acknowledge=True, max_iterations=1,
        app_mode="practice", account_id="", token="", enable_live=False,
    )
    assert code != 0
    assert "credential" in capsys.readouterr().err.lower()


def test_live_parser_requires_acknowledge_flag_for_arm():
    from forex_trader.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["live", "--arm", "--i-understand-this-places-orders"])
    assert args.command == "live"
    assert args.arm is True
    assert args.acknowledge is True


def test_live_command_executes_dry_run_ticks_via_injected_runner(capsys):
    from forex_trader.cli import run_live_command

    calls = {}

    def fake_runner(*, arm, max_iterations, sleep_seconds, account_id, token, app_mode):
        calls["arm"] = arm
        calls["iters"] = max_iterations
        # Pretend three dry-run ticks happened.
        return [("dry_run", "no signal")] * max_iterations

    code = run_live_command(
        arm=False, acknowledge=True, max_iterations=3,
        app_mode="practice", account_id="acct", token="tok", enable_live=False,
        runner=fake_runner,
    )

    out = capsys.readouterr().out
    assert code == 0
    assert calls["arm"] is False
    assert calls["iters"] == 3
    assert "dry_run" in out.lower()
    assert "3" in out


def test_seed_command_populates_trades_in_db(tmp_path):
    from forex_trader.cli import run_seed_command
    from forex_trader.storage.repositories import TradingRepository

    db = tmp_path / "seed.db"
    code = run_seed_command(db_path=str(db), days=3, seed=1)

    assert code == 0
    repo = TradingRepository(db)
    # The seeded backtest should have produced at least one trade story.
    assert len(repo.list_trade_stories()) >= 1


def test_seed_parser_accepts_options():
    from forex_trader.cli import build_parser

    args = build_parser().parse_args(["seed", "--days", "5", "--seed", "9"])
    assert args.command == "seed"
    assert args.days == 5
    assert args.seed == 9
