from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from datetime import datetime

from forex_trader.backtest.compare import format_comparison
from forex_trader.backtest.feed import generate_synthetic_candles, load_candles_csv
from forex_trader.backtest.runner import run_backtest
from forex_trader.config import Settings
from forex_trader.main import validate_startup
from forex_trader.strategy.base import Strategy
from forex_trader.strategy.eurusd_mean_reversion import EurUsdMeanReversionStrategy
from forex_trader.strategy.eurusd_opening_window import EurUsdOpeningWindowStrategy

STRATEGIES: dict[str, type[Strategy]] = {
    "opening_window": EurUsdOpeningWindowStrategy,
    "mean_reversion": EurUsdMeanReversionStrategy,
}

LiveRunner = Callable[..., list[tuple[str, str]]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forex-trader", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    bt = sub.add_parser("backtest", help="Run a backtest over CSV or synthetic candles.")
    bt.add_argument("--csv", help="Path to an OHLC CSV. Omit to use synthetic candles.")
    bt.add_argument("--count", type=int, default=1000, help="Synthetic candle count.")
    bt.add_argument("--seed", type=int, default=0, help="Synthetic random seed.")
    bt.add_argument("--start", default="2026-01-01T05:00:00+00:00", help="Synthetic start time.")
    bt.add_argument("--strategy", default="opening_window", choices=sorted(STRATEGIES))
    bt.add_argument("--session-start", default="05:00")
    bt.add_argument("--session-end", default="09:00")
    bt.add_argument("--session-tz", default="America/Mexico_City")

    ev = sub.add_parser("evidence", help="Backtest all strategies and write a verdict report.")
    ev.add_argument("--days", type=int, default=5, help="Fixture length in days.")
    ev.add_argument("--seed", type=int, default=0, help="Fixture random seed.")
    ev.add_argument(
        "--out", default="docs/reviews/strategy-evidence.md", help="Report output path."
    )
    ev.add_argument("--real", action="store_true",
                    help="Use real OANDA EUR/USD history instead of the fixture.")
    ev.add_argument("--granularity", default="M5", help="Real-candle granularity.")
    ev.add_argument("--count", type=int, default=5000, help="Real-candle count.")

    live = sub.add_parser(
        "live", help="Run the live practice loop (dry-run by default; --arm places orders)."
    )
    live.add_argument(
        "--arm", action="store_true",
        help="Actually place orders. Without this the loop is a dry run.",
    )
    live.add_argument(
        "--i-understand-this-places-orders", dest="acknowledge", action="store_true",
        help="Required acknowledgement to arm the loop.",
    )
    live.add_argument("--max-iterations", type=int, default=1, help="Number of ticks to run.")
    live.add_argument("--sleep-seconds", type=float, default=60.0)

    sd = sub.add_parser(
        "seed", help="Run a backtest into the database so the dashboard has data."
    )
    sd.add_argument("--db", help="Database path (defaults to DATABASE_PATH).")
    sd.add_argument("--days", type=int, default=10, help="Fixture length in days.")
    sd.add_argument("--seed", type=int, default=42, help="Fixture random seed.")
    sd.add_argument("--real", action="store_true",
                    help="Use real OANDA EUR/USD history instead of the fixture.")
    sd.add_argument("--granularity", default="M5", help="Real-candle granularity (M5, M15, H1...).")
    sd.add_argument("--count", type=int, default=5000, help="Real-candle count (max 5000/request).")

    an = sub.add_parser(
        "analyze",
        help="Walk-forward analysis on real OANDA history (US-open window).",
    )
    an.add_argument("--months", type=int, default=6, help="Months of history to fetch.")
    an.add_argument("--granularity", default="M5", help="Candle granularity.")
    an.add_argument("--window-start", default="08:30", help="Session start (ET).")
    an.add_argument("--window-end", default="11:30", help="Session end (ET).")
    an.add_argument("--out", default="docs/research/walk-forward-analysis.md")

    sub.add_parser("status", help="Print active mode and startup safety status.")
    return parser


def run_analyze_command(
    *,
    months: int = 6,
    granularity: str = "M5",
    window_start: str = "08:30",
    window_end: str = "11:30",
    out_path: str = "docs/research/walk-forward-analysis.md",
) -> int:
    import json
    from datetime import UTC, datetime, timedelta
    from pathlib import Path

    from forex_trader.analysis.market import analyze_window
    from forex_trader.analysis.walkforward import run_walk_forward
    from forex_trader.backtest.history_fetch import OandaHistoryFetcher
    from forex_trader.backtest.session_filter import filter_session_window

    settings = Settings.from_env()
    if not settings.oanda_api_token:
        print("analyze needs an OANDA token (set OANDA_API_TOKEN).", file=sys.stderr)
        return 1

    # NOTE: `now` is read once here for the fetch range; not used in cached logic.
    end = datetime.now(UTC)
    start = end - timedelta(days=30 * months)
    print(f"Fetching ~{months} months of {granularity} EUR/USD history...")
    fetcher = OandaHistoryFetcher(token=settings.oanda_api_token)
    raw = fetcher.fetch_range(granularity=granularity, start=start, end=end)
    window = filter_session_window(
        raw, tz="America/New_York", start_hhmm=window_start, end_hhmm=window_end
    )
    print(f"Fetched {len(raw)} candles; {len(window)} inside the US-open window.")

    stats = analyze_window(window)
    report = run_walk_forward(
        candles=window,
        reward_to_risk_grid=[1.0, 1.5, 2.0, 2.5, 3.0],
        max_spread_grid=[1.0, 1.5, 2.0, 3.0],
        min_trades=10,
        session_start_local=window_start,
        session_end_local=window_end,
        session_tz="America/New_York",
    )

    out = Path(out_path)
    if out.parent != Path("."):
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "# Walk-Forward Analysis (US-open window)\n\n"
        f"Window: {window_start}-{window_end} ET, {granularity}, ~{months} months "
        f"({len(window)} session candles).\n\n"
        "## Market stats (whole window)\n\n```json\n"
        + json.dumps(stats, indent=2)
        + "\n```\n\n## Walk-forward result\n\n```json\n"
        + json.dumps(
            {k: v for k, v in report.items() if k != "ranked"}, indent=2
        )
        + "\n```\n"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "ranked"}, indent=2))
    print(f"\nReport written to {out_path}")
    return 0


def run_seed_command(
    *,
    db_path: str | None = None,
    days: int = 10,
    seed: int = 42,
    use_real: bool = False,
    granularity: str = "M5",
    count: int = 5000,
) -> int:
    from forex_trader.backtest.history import resolve_candle_source
    from forex_trader.storage.repositories import TradingRepository

    settings = Settings.from_env()
    path = db_path or settings.database_path
    repository = TradingRepository(path)
    repository.clear_all()  # start from a clean slate for a fresh dashboard
    try:
        candles = resolve_candle_source(
            use_real=use_real, token=settings.oanda_api_token, days=days, seed=seed,
            granularity=granularity, count=count,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"Could not load candles: {exc}", file=sys.stderr)
        return 1
    source = f"real OANDA {granularity}" if use_real else "offline fixture"
    print(f"Loaded {len(candles)} candles ({source}).")
    result = run_backtest(
        candles=candles,
        repository=repository,
        # Honor the configured risk settings so the seeded data reflects the
        # operator's actual caps (e.g. a loosened or disabled daily-loss limit).
        max_risk_per_trade=settings.max_risk_per_trade,
        max_daily_loss=settings.max_daily_loss,
        max_open_positions=settings.max_open_positions,
        max_hold_minutes=settings.max_hold_minutes,
        session_start_local="00:00",
        session_end_local="23:59",
        session_tz="UTC",
    )
    # Enrich each story with the candle window spanning entry through exit so
    # the trade explorer can show the trade unfolding over time.
    from forex_trader.backtest.enrich import enrich_story_candles

    for story in repository.list_trade_stories():
        enriched = enrich_story_candles(story, candles, pad_before=10)
        repository.update_story_candles(story["position_id"], enriched["context_candles"])
    stories = repository.list_trade_stories()
    print(
        f"Seeded {path}: {len(stories)} trades, "
        f"{result.trades_closed} closed, ${result.total_realized_pnl:.2f} PnL.\n"
        f"View with: streamlit run src/forex_trader/dashboard/app.py"
    )
    return 0


def run_live_command(
    *,
    arm: bool,
    acknowledge: bool,
    max_iterations: int,
    app_mode: str,
    account_id: str,
    token: str,
    enable_live: bool,
    sleep_seconds: float = 60.0,
    runner: LiveRunner | None = None,
) -> int:
    """Validate every safety gate before the live loop may run.

    Refuses unless the mode is practice/live, credentials are present, (for
    live) live trading is explicitly enabled, and arming is acknowledged. This
    function performs the checks; the user runs it deliberately.
    """
    if app_mode not in {"practice", "live"}:
        print(
            f"live requires app_mode 'practice' or 'live', not {app_mode!r}.",
            file=sys.stderr,
        )
        return 1
    if not account_id or not token:
        print("live requires OANDA credentials in the environment.", file=sys.stderr)
        return 1
    if app_mode == "live" and not enable_live:
        print("live mode requires ENABLE_LIVE_TRADING=true.", file=sys.stderr)
        return 1
    if arm and not acknowledge:
        print(
            "Refusing to arm: pass --i-understand-this-places-orders to acknowledge "
            "that --arm places real orders.",
            file=sys.stderr,
        )
        return 1

    mode_label = "ARMED — placing orders" if arm else "DRY RUN — no orders"
    print(f"Live loop starting ({app_mode}, {mode_label}, {max_iterations} ticks)...")

    active_runner: LiveRunner
    if runner is None:
        from forex_trader.execution.live import run_oanda_live_loop

        active_runner = run_oanda_live_loop
    else:
        active_runner = runner

    results = active_runner(
        arm=arm,
        max_iterations=max_iterations,
        sleep_seconds=sleep_seconds,
        account_id=account_id,
        token=token,
        app_mode=app_mode,
    )
    for index, (status, reason) in enumerate(results, start=1):
        print(f"  tick {index}: {status} — {reason}")
    print(f"Live loop finished: {len(results)} ticks.")
    return 0


def run_evidence_command(
    *,
    days: int,
    seed: int,
    out_path: str,
    use_real: bool = False,
    granularity: str = "M5",
    count: int = 5000,
) -> int:
    from pathlib import Path

    from forex_trader.backtest.evidence import build_evidence_report
    from forex_trader.backtest.history import resolve_candle_source

    candles = None
    source_label = None
    if use_real:
        settings = Settings.from_env()
        try:
            candles = resolve_candle_source(
                use_real=True, token=settings.oanda_api_token, days=days, seed=seed,
                granularity=granularity, count=count,
            )
        except (ValueError, RuntimeError) as exc:
            print(f"Could not load real candles: {exc}", file=sys.stderr)
            return 1
        source_label = (
            f"real OANDA EUR/USD history ({len(candles)} {granularity} candles, "
            f"{candles[0].time.date()} to {candles[-1].time.date()})"
        )

    table, report = build_evidence_report(
        days=days, seed=seed, candles=candles, source_label=source_label
    )
    out = Path(out_path)
    if out.parent != Path("."):
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n")
    print(format_comparison(table))
    print(f"\nReport written to {out_path}")
    return 0


def run_backtest_command(
    *,
    count: int,
    seed: int,
    strategy: str,
    session_start: str,
    session_end: str,
    session_tz: str,
    start: str,
    csv: str | None = None,
) -> int:
    strategy_cls = STRATEGIES.get(strategy)
    if strategy_cls is None:
        print(f"Unknown strategy: {strategy}", file=sys.stderr)
        return 1

    if csv:
        candles = load_candles_csv(csv)
    else:
        candles = generate_synthetic_candles(
            start=datetime.fromisoformat(start), count=count, seed=seed
        )

    result = run_backtest(
        candles=candles,
        strategy=strategy_cls(),
        session_start_local=session_start,
        session_end_local=session_end,
        session_tz=session_tz,
    )
    print(
        f"Backtest [{strategy}] over {len(candles)} candles\n"
        f"  trades closed : {result.trades_closed} "
        f"(wins {result.wins} / losses {result.losses})\n"
        f"  trades blocked: {result.trades_blocked}\n"
        f"  win rate      : {result.win_rate:.1%}\n"
        f"  expectancy    : ${result.expectancy:.2f} / trade\n"
        f"  realized PnL  : ${result.total_realized_pnl:.2f}\n"
        f"  max drawdown  : ${result.max_drawdown:.2f}\n"
        f"  final equity  : ${result.final_equity:.2f}"
    )
    return 0


def run_status_command() -> int:
    settings = Settings.from_env()
    status = validate_startup(settings)
    print(f"Mode: {settings.app_mode}")
    print(f"Symbol: {settings.trade_symbol}")
    print(f"Max risk/trade: {settings.max_risk_per_trade:.4%}")
    print(f"Startup: {'OK' if status.ok else 'BLOCKED'} — {status.reason}")
    return 0 if status.ok else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "backtest":
        return run_backtest_command(
            count=args.count,
            seed=args.seed,
            strategy=args.strategy,
            session_start=args.session_start,
            session_end=args.session_end,
            session_tz=args.session_tz,
            start=args.start,
            csv=args.csv,
        )
    if args.command == "evidence":
        return run_evidence_command(
            days=args.days, seed=args.seed, out_path=args.out,
            use_real=args.real, granularity=args.granularity, count=args.count,
        )
    if args.command == "live":
        settings = Settings.from_env()
        return run_live_command(
            arm=args.arm,
            acknowledge=args.acknowledge,
            max_iterations=args.max_iterations,
            app_mode=settings.app_mode,
            account_id=settings.oanda_account_id,
            token=settings.oanda_api_token,
            enable_live=settings.enable_live_trading,
            sleep_seconds=args.sleep_seconds,
        )
    if args.command == "seed":
        return run_seed_command(
            db_path=args.db, days=args.days, seed=args.seed,
            use_real=args.real, granularity=args.granularity, count=args.count,
        )
    if args.command == "analyze":
        return run_analyze_command(
            months=args.months, granularity=args.granularity,
            window_start=args.window_start, window_end=args.window_end,
            out_path=args.out,
        )
    if args.command == "status":
        return run_status_command()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
