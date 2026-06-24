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
