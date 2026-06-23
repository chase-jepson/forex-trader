# Forex Trader

Forex Trader is a local-first `EUR/USD` trading research and simulation system. It is built to learn safely before it ever talks to a live broker: first-principles notes, deterministic strategy rules, hard risk checks, simulated execution, trade reviews, and reporting all come before OANDA practice mode.

## Modes

- `simulated`: uses an in-memory broker and fake fills. This is the default.
- `practice`: uses broker demo credentials after the simulator is useful and reviewable.
- `live`: intentionally disabled unless explicit safety gates are complete.

## Safety Philosophy

- The LLM can explain trades and summarize reviews, but it cannot place orders or change rules.
- Every trade plan must pass the risk engine before the broker adapter sees it.
- Every trade and blocked trade should produce a review record.
- Default risk is `0.25%` of equity per trade.
- `EUR/USD` is the only v1 instrument.

## What's Built

- **Research foundation** — glossary, forex basics, EUR/USD market map, strategy hypotheses, validation checklist.
- **Risk engine** — hard guardrails (required stop, target/timed exit, one open position, max hold, daily-loss cap, max risk/trade) enforced before any order.
- **Simulated broker** — realistic fills (buys at ask, sells at bid), spread cost, exact stop/target fills, and a shared pip-value model so sizing and PnL reconcile.
- **Strategy gate** — research registry gates strategies; nothing runs until marked `ready_for_sim`. Default fallback is `NullStrategy`.
- **Strategies** — `eurusd_opening_window` (ready), plus draft `eurusd_mean_reversion` and a `news_avoidance` filter.
- **Execution + audit trail** — every cycle persists to SQLite, including blocked trades with their exact rejection reason.
- **Trade reviews** — every completed and blocked trade gets a review record with mistake tags and an improvement hypothesis.
- **Backtest harness** — run a strategy over CSV or seeded synthetic candles; reports equity curve, win rate, expectancy, and max drawdown. Compare strategies side by side.
- **OANDA practice adapter** — mocked contract tests plus credential-gated read-only integration tests against the live fxPractice API.
- **Mode gates** — `simulated` / `practice` / `live`, with live disabled by default behind explicit flags and completed-gate checks.
- **Streamlit dashboard** — live market, trade reviews, and reports read from the persisted database.

## Local Commands

Requires Python 3.12 or newer. Install first:

```bash
pip install -e ".[dev]"
```

Run a backtest, gather strategy evidence, or check status:

```bash
forex-trader backtest --count 2000 --seed 42 --strategy opening_window
forex-trader backtest --csv data/eurusd.csv --strategy mean_reversion
forex-trader evidence --days 10 --seed 42   # backtests all strategies, writes a verdict report
forex-trader status
```

Run the live practice loop (dry-run by default; never auto-armed — see
[docs/live-mode.md](docs/live-mode.md) for the safety model and checklist):

```bash
forex-trader live --max-iterations 5                                   # dry run, no orders
forex-trader live --arm --i-understand-this-places-orders              # places demo orders
```

Tests, dashboard, and live OANDA checks:

```bash
python -m pytest -v                       # hermetic suite (no network)
python -m pytest -m integration           # live OANDA practice checks (needs .env creds)
forex-trader seed                         # populate the dashboard with backtest data
python -m streamlit run src/forex_trader/dashboard/app.py
```

The dashboard (Trade Explorer, reviews, equity curve) is documented in
[docs/dashboard.md](docs/dashboard.md) — click any trade to see its chart and
the reasoning behind it.

## Configuration

Copy `.env.example` to `.env` and fill in values. `Settings.from_env()` loads it
(real shell exports win over the file). OANDA practice mode needs
`OANDA_ACCOUNT_ID` and `OANDA_API_TOKEN`. `.env` is gitignored — never commit
credentials.

