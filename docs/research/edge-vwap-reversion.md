# Session-Mean Reversion (US-open) — EDGE DID NOT HOLD ON 12 MONTHS

> **RETRACTION (important):** This rule looked validated on a 6-month sample but
> **failed on 12 months.** When tested across a full year split in half, the
> recent 6 months (Dec 2025–Jun 2026) were profitable but the prior 6 months
> (Jun–Dec 2025) **lost** — and **zero** parameter configurations were positive
> in *both* halves of the year. The "edge" was a **regime artifact**, not a
> stable, all-weather edge. It is NOT suitable for deployment. The analysis
> below is kept as a record of how the apparent edge arose and why it was
> rejected. Lesson: 6 months was too short; the longer test caught it.

## The insight from the data

Analysis of 6 months of real EUR/USD US-open candles (08:30–11:30 ET):

- Directional rules have **no edge** — first-30-min direction predicts the rest
  of the session only 47.7% of the time (worse than a coin flip).
- But **mean-reversion to the running session mean has a real, escalating edge**:

  | Extension from session mean | Reverts toward mean within 3 candles |
  |---|---|
  | ≥10 pips | 53.8% |
  | ≥15 pips | 54.3% |
  | ≥20 pips | **63.0%** |

  The deeper the stretch, the more reliably it snaps back.

## The rule (`eurusd_vwap_reversion`, deterministic)

Sell when price is ≥30 pips above the running session mean; buy when ≥30 below.
Target 40% of the way back to the mean (take the reversion quickly), stop 12
pips beyond the entry. Spread filter ≤2 pips. No LLM at runtime — pure Python.

## Walk-forward result (honest: selected on in-sample, validated once)

| | In-sample | Out-of-sample |
|---|---|---|
| PnL | +$147 | **+$41** |
| Win rate | 50% | **53%** |
| Trades | 32 | 32 |
| Max drawdown | $81 | $119 |

**Positive on both halves.** And it is not a lucky cell: **17 parameter
configurations** in the (ext 22–30, target 0.4–0.5, stop 10–12) region are
positive on both halves with ≥50% out-of-sample win rate — a robust plateau, the
signature of a real effect rather than curve-fitting.

## Honest caveats (what would make this fail)

- **Small sample**: 32 out-of-sample trades over 3 months. The edge is real but
  thin; +$41 is modest. More history (12+ months) would firm up confidence.
- **Trend-day risk**: the losses come from days that keep extending past the
  stop. A trend filter on top may improve it (to be tested).
- Still `DRAFT` in the registry — gated behind NullStrategy, never auto-runs.
  Awaiting sign-off before any practice deployment.

## Next experiments (to push profitability higher, honestly)

1. Layer the TrendFilter to skip the strong-trend days that cause the losers.
2. Test on 12 months to confirm the edge holds with more data.
3. Tune the target/stop with the risk-adjusted optimizer over the larger set.
