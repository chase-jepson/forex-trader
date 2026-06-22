# Evidence → Harden → Live Practice Loop — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Gather strategy evidence from real/realistic historical data, harden the engine for unattended operation, then build a live OANDA-practice run loop that is fully tested but disabled by default and never auto-run.

**Architecture:** Three sequential phases. (A) A historical-data layer feeding the existing backtest harness, producing a comparison report. (B) Operational safety: structured logging, file-based emergency stop, startup health checks against OANDA, position reconciliation, run-state persistence. (C) A `LiveTrader` run loop that reuses the existing orchestrator/risk/broker, polls OANDA pricing, and places practice orders — gated behind `ENABLE_LIVE_TRADING` + `app_mode` and an explicit CLI opt-in, with emergency-stop honored each tick.

**Tech Stack:** Python 3.12+, stdlib only where possible (urllib, logging, sqlite3), pytest/ruff/mypy-strict. Existing modules: `execution/orchestrator.py`, `broker/oanda.py`, `broker/simulated.py`, `backtest/`, `config.py`, `main.py`.

**Safety invariant (non-negotiable):** The live loop's order-placing path must be built and tested but NOT executed against the real account autonomously. Running it is the user's action.

---

## Phase A — Strategy Evidence

### Task A1: Historical candle source

**Files:**
- Create: `src/forex_trader/backtest/history.py`
- Test: `tests/test_history.py`

Provide a function that returns a realistic multi-day EUR/USD candle series for backtesting. Prefer a no-auth source; if unavailable offline, generate a realistic fixture (seeded, with intraday session structure) and clearly label it synthetic. Must reuse the existing `Candle` model and be deterministic for tests.

**Steps:** TDD — failing test for shape/determinism → implement → pass → commit.

### Task A2: Evidence report command

**Files:**
- Modify: `src/forex_trader/cli.py` (add `evidence` subcommand)
- Modify: `src/forex_trader/backtest/compare.py` if needed
- Test: `tests/test_cli.py` (extend)

Run all three strategies over the same history via `compare_strategies`, print the `format_comparison` table plus a one-line verdict per strategy (edge / no edge / insufficient trades). Write the report to `docs/reviews/strategy-evidence.md`.

**Steps:** TDD per the CLI pattern already established.

---

## Phase B — Harden for Unattended Operation

### Task B1: Structured logging

**Files:**
- Create: `src/forex_trader/obs/logging.py`
- Test: `tests/test_logging.py`

A `get_logger(name)` helper using stdlib `logging` with a consistent format; no secrets ever logged (assert token never appears). Wire into orchestrator decision points and broker calls.

### Task B2: Emergency stop workflow

**Files:**
- Create: `src/forex_trader/safety/emergency.py`
- Test: `tests/test_emergency.py`

`is_emergency_stopped(path)` and `trip_emergency_stop(path)` / `clear_emergency_stop(path)`. The live loop checks this every tick before placing any order. `config.emergency_stop_path` already exists.

### Task B3: OANDA startup health check

**Files:**
- Modify: `src/forex_trader/broker/oanda.py` (add `health_check()` — account summary fetch, read-only)
- Modify: `src/forex_trader/main.py` (`validate_startup` optionally calls broker health when practice/live)
- Test: `tests/test_oanda_contract.py` (mocked) + integration variant

### Task B4: Position reconciliation

**Files:**
- Create: `src/forex_trader/execution/reconcile.py`
- Test: `tests/test_reconcile.py`

Compare broker-reported open positions vs locally-tracked state; surface mismatches (the live loop refuses to open new trades if reconciliation disagrees). Read-only.

### Task B5: Run-state persistence

**Files:**
- Modify: `src/forex_trader/storage/repositories.py` (add a `run_state` table: last tick time, cumulative pnl, day boundary)
- Test: `tests/test_run_state.py`

So a restarted loop resumes daily-pnl/day-boundary correctly instead of resetting silently.

---

## Phase C — Live Practice Run Loop (built, tested, NOT auto-run)

### Task C1: LiveTrader tick

**Files:**
- Create: `src/forex_trader/execution/live.py`
- Test: `tests/test_live_trader.py` (using a fake broker — NO network)

`LiveTrader.tick(now)`: check emergency stop → reconcile → fetch quote → build window from recent candles → `orchestrator.run_cycle` → `resolve_stop_target_fills` / `close_expired_positions`. All order placement flows through the existing risk engine. Fully tested against `SimulatedBroker`/a fake — never the real account in tests.

### Task C2: LiveTrader loop + CLI wiring

**Files:**
- Modify: `src/forex_trader/execution/live.py` (a `run()` that ticks on an interval with a max-iterations guard)
- Modify: `src/forex_trader/cli.py` (add `live` subcommand)
- Test: `tests/test_cli.py`

The `live` subcommand REFUSES to start unless `app_mode in {practice, live}`, credentials present, `ENABLE_LIVE_TRADING` true (for live), and a `--i-understand-this-places-orders` flag is passed. Default run is a dry-run that logs intended actions without placing orders unless `--arm` is given.

### Task C3: Documentation + final verification

**Files:**
- Modify: `README.md`, `docs/` (live-mode operating guide, safety checklist)

**STOP POINT:** Do not execute `forex-trader live --arm` against the real account. Leave it for the user.

---

## Verification (every task)
- `.venv/bin/python -m pytest -q` (hermetic), `ruff check .`, `mypy src` — all green before commit.
- Integration tests (`pytest -m integration`) stay read-only and credential-gated.
- Commit per task, conventional commits, push to origin/main.
