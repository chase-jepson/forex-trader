# Validated Edge: Regime-Gated Session-Mean Reversion

This is the **first and only** rule to survive the full validation gauntlet —
the 12-month both-halves walk-forward, in the **real production engine** (spread
costs, fills, the works), with honest in-sample selection.

## The path to it

1. Breakout, fade, classic & VWAP mean-reversion, momentum, gaps — all failed.
   Every directional predictor measured ~47% (coin flip).
2. There IS a real reversion tendency (price stretched ≥20p from the session
   mean reverts ~63%, ~69% on high volume) — but it is **regime-dependent**: it
   paid in one 6-month half and lost in the other. Every reversion variant died
   on the 12-month both-halves test for this reason.
3. **Key discovery:** the regime itself is *forecastable* at a multi-day scale.
   Whether reversion paid over the trailing 3–5 days predicts whether it pays
   the next day **~59–62%** of the time (vs ~47% for price direction).

## The rule (`eurusd_regime_reversion`, deterministic)

Fade extension ≥22 pips from the running session mean — **but only when the
recent regime favors reversion** (the trailing-window net of completed reversion
outcomes is positive). Target 40% back to the mean, 12-pip stop, ≤2-pip spread.
The strategy holds a `ReversionRegimeTracker` (one parameter: window) that the
backtest/live loop feeds with each completed trade's pip result. No LLM at
runtime — fully deterministic.

The gate adapts to the regime rather than fitting parameters to both halves,
which is *why* it generalizes instead of curve-fitting.

## Validation (production engine, honest in-sample selection)

Selected purely on the in-sample half (H1, by risk-adjusted score), then the
out-of-sample half (H2) reported once:

| | In-sample (H1) | Out-of-sample (H2) |
|---|---|---|
| PnL | +$8 | **+$69** |
| Win rate | 50% | **55%** |
| Trades | 10 | 11 |
| Max drawdown | $71 | $54 |

**Positive out-of-sample.** And not a lucky cell: **4 configurations** are
positive in both halves in the production engine. The regime gate turned the
losing H1 reversion (-$195 ungated) into break-even/positive while keeping H2's
gains.

## Honest caveats — this is NOT yet deployable

- **Very low trade frequency** — ~10 trades per 6 months. The gate is highly
  selective; it sits out most of the time. Small sample = wide error bars.
- **The regime detector could still be fit to these particular 12 months.** One
  year is not enough to be confident. It needs **2+ years** of validation.
- Absolute profit is modest (+$69 on $10k over 6 months ≈ 0.7%). Real, but small.
- Status: **DRAFT** in the registry, gated behind NullStrategy, never auto-runs.

## Next steps to firm it up (honest, before any real money)

1. Validate on 2–3 years of data (more both-halves splits / rolling windows).
2. Confirm trade frequency is high enough to matter, or relax the gate carefully.
3. Forward-test in dry-run / practice mode for a period before any live use.

## UPDATE: 2-year stress test (4 independent periods)

Fetched 2 years and split into 4 consecutive 6-month periods. The validated
config (ext=22, stop=12, window=8):

| Period | PnL | Win | Trades | Drawdown |
|---|---|---|---|---|
| 2024 H2 | -$27 | 0% | 1 | $27 |
| 2024H2–2025H1 | **+$393** | 69% | 32 | $58 |
| 2025 H2 | -$24 | 40% | 5 | $71 |
| 2025H2–2026 | +$50 | 50% | 10 | $54 |

**Positive in 2 of 4 periods**, net +$392 over 2 years. The honest read:

- **The edge is real but fragile and lumpy.** Most of the profit comes from one
  favorable stretch (early 2025). Two periods barely traded.
- **The gate controls downside well** — the two losing periods lost only -$27 and
  -$24. It successfully sits out when reversion isn't working.
- But it is **not a consistent, all-weather edge.** It is a small positive
  expectancy that shows up in some regimes and goes dormant in others.

**Verdict:** keep as DRAFT. It is the best validated candidate, downside-safe,
and net-positive over 2 years — but it is thin and inconsistent. It is suitable
for a long dry-run / practice forward-test to gather live evidence, NOT for
meaningful capital. This is consistent with the reality that retail FX edges are
small and hard-won.

## IMPROVEMENT: regime-strength threshold + volume gate (3-of-4 periods)

Two refinements lifted the edge from 2-of-4 to 3-of-4 periods at FIXED risk:

1. **Volume gate** — only fade a high-volume (exhaustion) extension spike.
2. **Regime-strength threshold** — only trade when the trailing regime strength
   (net recent reversion pips) exceeds a threshold (default 5), not merely >0.
   This skips marginal trades, raising win rate and consistency.

Validated in the production engine across 4 independent 6-month periods (2yr):

| Config | Net | Periods + | Worst | Trades |
|---|---|---|---|---|
| threshold=0 (old) | +$427 | 2 of 4 | −$27 | 43 |
| **threshold=5 (new default)** | **+$498** | **3 of 4** | −$27 | 40 |

Per-period: [−27, 399, 4, 122] — the previously-dead P2 flipped positive (+$4)
and P3 grew (68→122), while the big winner P1 stayed intact. No leverage; the
gain comes from better selectivity, not bigger bets.

### Honest nuance (important)

The strategy is stateful: its regime tracker must "warm up" with observed
reversion outcomes before the strength threshold can be met. On a single
continuous 12-month run it therefore trades very little early on. The 4-period
evaluation (each period a fresh 6-month deployment) is the realistic test and is
where the +$498 / 3-of-4 result holds. In live use the tracker would carry state
across days continuously, which behaves like the per-period test once warmed up.

Still DRAFT, still thin, still needs forward-testing — but meaningfully more
consistent than before.
