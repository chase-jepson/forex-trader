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
