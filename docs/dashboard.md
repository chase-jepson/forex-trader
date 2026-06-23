# Dashboard Guide

The local Streamlit dashboard visualizes the agent's trades, lets you inspect
why each one was taken, and tracks performance over time.

## Viewing it

From the project root:

```bash
pip install -e ".[dev]"            # once, if not already installed
python -m streamlit run src/forex_trader/dashboard/app.py
```

It opens `http://localhost:8501` automatically (and prints the URL). Press
`Ctrl+C` in the terminal to stop. Streamlit auto-reloads on file changes.

## Getting data into it

The dashboard reads from the database at `DATABASE_PATH` (default
`data/forex-trader.db`). If it looks empty, populate it:

```bash
forex-trader seed --days 15 --seed 42
```

`seed` runs a backtest over a realistic fixture into the database, producing
trades, reviews, reports, and an equity curve. Re-running `seed` clears prior
data first. (Fixture data has no real edge — it exists so the dashboard has
something to show; point the loop at real history for meaningful results.)

Dry runs of the live loop also persist "would-have-traded" observations
(marked `[dry-run]`), so evidence accrues against live pricing without trading:

```bash
APP_MODE=practice forex-trader live --max-iterations 20 --sleep-seconds 60
```

## Sections

- **Live Market** — latest quote/status from the most recent cycle.
- **Trade Explorer** — the centerpiece. Pick any trade from the list to see:
  - a candlestick chart with the **entry, stop, target, and exit** marked,
  - the candle window spanning **before entry through the close**, so you can
    watch the trade unfold,
  - "what the agent saw": the signal reasoning that made it expect success,
  - the signal metadata and risk decision behind the trade.
  Dry-run observations are tagged `[dry-run]`.
- **Trade Reviews** — every completed trade's review with mistake tags. Routine
  capacity blocks (position limit, daily-loss halt) are intentionally excluded
  so the log stays meaningful.
- **Reports** — metric cards (trades, win rate, realized PnL, avg hold) and the
  **equity curve** built from realized PnL over closed trades.
