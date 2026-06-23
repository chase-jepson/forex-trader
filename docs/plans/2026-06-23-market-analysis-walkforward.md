# Market Analysis + Walk-Forward Optimization Plan

> **For Claude:** REQUIRED SUB-SKILL: superpowers:executing-plans.

**Goal:** Fetch ~6 months of real EUR/USD history, focus on the US-open window
(08:30–11:30 ET), analyze the first 3 months to find/optimize profitable rules,
then validate on the held-out 3 months (out-of-sample) to confirm a real edge.

**Method:** Train/test split with walk-forward validation. Optimize ONLY on the
in-sample window; report in-sample vs out-of-sample separately so curve-fitting
is visible. Never auto-arm; suggestions + draft strategy only.

**LLM:** Deterministic analysis engine (free, tested). I reason over its output
via the Max plan in-session. ANTHROPIC_API_KEY is in .env for later unattended
use but not required now.

---

## Phase M1: Multi-page history fetch
- [ ] `fetch_oanda_history(token, instrument, granularity, start, end)` that
      pages backward via the `to=` param to assemble an arbitrary date range
      (>5000 candles). Dedup + sort. Cache to disk (data/history/) to avoid
      re-fetching. TDD with a fake _request.

## Phase M2: Session-window filter
- [ ] `filter_session_window(candles, tz, start_hhmm, end_hhmm)` keeping only
      candles inside a daily local window. Default US-open: America/New_York
      08:30–11:30. TDD.

## Phase M3: Train/test split
- [ ] `split_by_date(candles, split_date)` -> (in_sample, out_of_sample). TDD.

## Phase M4: Market analysis engine (deterministic, free)
- [ ] `analyze_window(candles)` -> stats: average range, directional bias,
      breakout follow-through rate, volatility by half-hour bucket, gap stats.
      Pure functions, fully tested. This is what I reason over to propose rules.

## Phase M5: Parameterized opening-window strategy + optimizer
- [ ] Make the opening-window strategy params (range minutes, breakout buffer,
      reward:risk, max spread) tunable.
- [ ] `optimize(in_sample, grid)` -> best param set by total PnL (with a trade
      floor to avoid 1-lucky-trade fits). Reports top N. TDD on a tiny grid.

## Phase M6: Walk-forward report
- [ ] Run best in-sample params on out-of-sample; produce a report comparing
      in-sample vs out-of-sample PnL/win-rate/expectancy. Honest overfit check.
- [ ] `forex-trader analyze --months 6 --split 3` CLI command.

## Phase M7: Suggest + scaffold draft strategy
- [ ] Write findings + proposed rules to docs/research/.
- [ ] Scaffold a draft strategy from the winning params, marked `draft` in the
      research registry (gated behind NullStrategy; never auto-runs).

## Verify every phase: pytest -q, ruff, mypy strict. Commit + push.
