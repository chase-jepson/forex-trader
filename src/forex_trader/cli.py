from __future__ import annotations

import argparse
import sys
from datetime import datetime

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

    sub.add_parser("status", help="Print active mode and startup safety status.")
    return parser


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
    if args.command == "status":
        return run_status_command()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
