# Forex Trader — Autonomous Work Plan

Goal: trustworthy local-first EUR/USD research system. Fix all review issues,
then build the 4 directions (backtest harness, OANDA practice, sim fidelity,
strategy research). Run until clear work is exhausted. Commit per chunk, no push.

## Phase 1 — Fix review issues

### HIGH
- [x] H1: pip/spread-aware PnL — reconcile sizing & PnL via a single pip-value model
- [x] H2: timezone-correct session logic (local cutoff vs UTC `now`)
- [x] H3: OANDA read-back/close fabricates fields — raise NotImplementedError instead of wrong data

### MEDIUM
- [x] M1: wire `daily_realized_pnl` into the orchestrator so the daily-loss cap is live
- [x] M2: forced-close should record SCRATCH for flat exits, not "loss"
- [x] M3: enforce session window on entries (`can_open_new_trade` is never called)

### LOW / nits
- [x] L1: remove or use `summarize_review` (llm/reviewer.py)
- [x] L2: remove `scheduler.py` dead indirection (or justify it)
- [x] L3: README python3.13 vs pyproject >=3.12 inconsistency

## Phase 2 — Sim fidelity (Direction 3)
- [x] Spread/slippage cost model on entry & exit
- [x] Intra-bar stop/target fill resolution
- [x] Continuous candle feed simulator

## Phase 3 — Backtest harness (Direction 1)
- [x] CSV candle loader + synthetic generator
- [x] Backtest runner over historical candles -> persisted cycles/reviews
- [x] Backtest report (equity curve, win rate, expectancy, max drawdown)

## Phase 4 — OANDA practice (Direction 2)
- [x] Real position read-back with correct fields
- [x] Real close with correct side/units/pnl
- [x] Live pricing loop wiring

## Phase 5 — Strategy research (Direction 4)
- [x] eurusd_mean_reversion strategy
- [x] eurusd_news_avoidance filter
- [x] strategy comparison framework

## Verification (every chunk)
- pytest -q, ruff check ., mypy src — all green before commit
