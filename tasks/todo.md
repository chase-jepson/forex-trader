# Forex Trader — Autonomous Work Plan

Goal: trustworthy local-first EUR/USD research system. Fix all review issues,
then build the 4 directions (backtest harness, OANDA practice, sim fidelity,
strategy research). Run until clear work is exhausted. Commit per chunk, no push.

## Phase 1 — Fix review issues

### HIGH
- [ ] H1: pip/spread-aware PnL — reconcile sizing & PnL via a single pip-value model
- [ ] H2: timezone-correct session logic (local cutoff vs UTC `now`)
- [ ] H3: OANDA read-back/close fabricates fields — raise NotImplementedError instead of wrong data

### MEDIUM
- [ ] M1: wire `daily_realized_pnl` into the orchestrator so the daily-loss cap is live
- [ ] M2: forced-close should record SCRATCH for flat exits, not "loss"
- [ ] M3: enforce session window on entries (`can_open_new_trade` is never called)

### LOW / nits
- [ ] L1: remove or use `summarize_review` (llm/reviewer.py)
- [ ] L2: remove `scheduler.py` dead indirection (or justify it)
- [ ] L3: README python3.13 vs pyproject >=3.12 inconsistency

## Phase 2 — Sim fidelity (Direction 3)
- [ ] Spread/slippage cost model on entry & exit
- [ ] Intra-bar stop/target fill resolution
- [ ] Continuous candle feed simulator

## Phase 3 — Backtest harness (Direction 1)
- [ ] CSV candle loader + synthetic generator
- [ ] Backtest runner over historical candles -> persisted cycles/reviews
- [ ] Backtest report (equity curve, win rate, expectancy, max drawdown)

## Phase 4 — OANDA practice (Direction 2)
- [ ] Real position read-back with correct fields
- [ ] Real close with correct side/units/pnl
- [ ] Live pricing loop wiring

## Phase 5 — Strategy research (Direction 4)
- [ ] eurusd_mean_reversion strategy
- [ ] eurusd_news_avoidance filter
- [ ] strategy comparison framework

## Verification (every chunk)
- pytest -q, ruff check ., mypy src — all green before commit
