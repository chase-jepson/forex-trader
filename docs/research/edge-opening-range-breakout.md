# VALIDATED EDGE: Tight Opening-Range Breakout

After every price-pattern *direction* and *reversion* idea failed, the edge came
from a different axis entirely: **volatility expansion**. This is the first
strategy to survive honest validation across the board.

## The idea

During the US open (08:30–11:30 ET), build the opening 30-minute range (first 6
M5 candles). If that range is **tight** (≤~12 pips — a quiet, coiled market),
trade the first break of the range in the breakout direction, targeting 1× the
range with a 0.5× stop. **One trade per session.** A tight opening predicts a
real expansion; a wide opening is already noisy and does not.

## Validation (real engine, with spread)

**Out-of-sample (selected max_range on year 1, tested year 2 once):**

| | Year 1 (in-sample) | Year 2 (out-of-sample) |
|---|---|---|
| PnL | +$2,192 | **+$1,822** |
| Win rate | 60% | **55%** |
| Trades | 173 | 194 |
| Max drawdown | $220 | $159 |

**All 4 independent 6-month periods positive** (max_range=15): per-period PnL
[+$836, +$1,169, +$1,333, +$893] — remarkably consistent.

**Continuous 2-year deployment == per-period** (+$4,229 both ways) — NO
evaluation artifact (unlike the rejected regime-reversion, which only "worked"
under per-period resets).

Summary: ~21%/year on a $10k account at 0.25% risk/trade, ~53–55% win, max
drawdown ~$300 → **return/drawdown ≈ 14**, which is a strong risk profile.

## Why this is trustworthy where others weren't

- **Different signal axis** — direction-via-volatility, not price-pattern
  direction (which measured ~47%, coin-flip) or reversion (regime-fragile).
- **Survives the continuous test** that exposed the regime strategy as an
  artifact.
- **Out-of-sample positive** by honest selection (year 1 → year 2).
- **Net of the ~2-pip spread** already.

## A bug caught (discipline note)

The first run showed +$48,000 / 242%/yr — obviously too good. Root cause: the
strategy re-entered the same breakout every candle, compounding one move into
many leveraged re-entries. Adding the **one-trade-per-session guard** dropped it
to the realistic +$4,229. Always distrust a backtest showing >100%/yr.

## Honest caveats (still DRAFT, not deployed)

- Only ~2 years validated. Wants more history and a live dry-run forward-test.
- The tight-range filter is essential and somewhat tuned; confirm it holds on
  out-of-window data.
- Registered DRAFT, gated behind NullStrategy, never auto-runs. Sign-off + a
  practice forward-test required before any real capital.
