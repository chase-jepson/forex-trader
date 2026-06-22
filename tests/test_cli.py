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
