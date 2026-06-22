# Backtesting

The backtest harness steps a strategy through historical candles using the
**same** orchestrator, risk engine, broker fill model, and review flow as live
execution. This keeps backtest evidence comparable to simulated and practice
runs — there is no separate, more-optimistic backtest path.

## Inputs

- **CSV candles** — `--csv path.csv` with columns `time,open,high,low,close`
  (`time` is ISO-8601). Loaded by `backtest.feed.load_candles_csv`.
- **Synthetic candles** — a deterministic seeded random walk via
  `backtest.feed.generate_synthetic_candles`. The same seed always yields the
  same series, so backtests are reproducible. Useful for exercising the
  machinery; it is **not** a claim of a real edge.

## What it models

- Fills at bid/ask with a configurable half-spread (so a flat round trip loses
  the spread).
- Intra-bar stop-loss / take-profit fills. When a single candle spans both, the
  stop resolves first (pessimistic convention — we cannot see intra-bar order).
- Forced exits at max hold time and session cutoff.
- The full risk gate on every entry, including the session window and
  daily-loss cap.

## Metrics

`BacktestResult` reports: trades closed/blocked, wins/losses, win rate,
expectancy per trade, total realized PnL, max drawdown (peak-to-trough in
account currency), and the equity curve.

## Running

```bash
forex-trader backtest --count 2000 --seed 42 --strategy opening_window \
  --session-start 00:00 --session-end 23:59 --session-tz UTC
```

## Comparing strategies

`backtest.compare.compare_strategies` runs several named strategies over the
identical candles and risk settings; `format_comparison` renders a side-by-side
table. Because every strategy shares the same engine, the numbers are directly
comparable.
