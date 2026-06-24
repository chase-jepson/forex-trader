# Edge Search Log (full-autonomy deep search)

Systematic attack on finding a concrete, consistently-profitable, deterministic
rule. Validation bar: positive across 4 independent 6-month periods over 2 years
(not just one split). All on EUR/USD US-open (08:30–11:30 ET) unless noted.

## Tested and their result (net over 2yr / periods positive)

| Angle | Result | Verdict |
|---|---|---|
| Regime-gated reversion (baseline) | +$393 / 2 of 4 | best so far |
| + volume confirmation (mult 1.2) | +$422 / 2 of 4 | marginal gain |
| Exit grid (target 0.3–1.0, stop 8–16) | best tgt=0.5 stop=12 → +$427 / 2 of 4 | tight target essential; letting winners run KILLS it |
| Trend-following (any params) | −$857 to −$2093 every period | no trend regime to exploit; bleeds spread |
| Other pairs (GBP, AUD) | GBP −$103 / 0–4, AUD +$38 / 1–4 | edge does NOT transfer; EUR/USD is best |
| Wider session (London+NY 03–12 ET) | best +$132 / 1 of 4 | worse; US-open window IS special |

## Why it stays at 2-of-4 periods

Reversion rate varies by period: P0 59%, P1 52%, P2 **48%**, P3 63%. The
strategy profits when reversion is strong and the regime gate correctly sits out
when it is weak (P2 was sub-coin-flip — a choppy, not trending, regime, so
trend-following doesn't help either). The dead periods don't lose much (−$27
worst) — the gate protects downside — but there is no profit to extract there
with a simple rule.

## Current best (deterministic, validated)

`eurusd_regime_reversion` with ext=22, target_fraction=0.5, stop=12, regime
window=8, volume_mult=1.2: net ~+$427 over 2 years, positive in 2 of 4 periods,
worst period −$27. Real but thin; downside-controlled.

## Still to try

- Gate responsiveness (faster regime adaptation to catch P2-style shifts)
- Session high/low (not mean) as reversion anchors
- Multi-candle exhaustion confirmation
- Position sizing by regime confidence (bet more when regime strongly favors)

## More angles (continued)

| Angle | Result | Verdict |
|---|---|---|
| Regime-strength threshold (>5 not >0) + volume gate | +$498 / 3 of 4, worst −$27 | **REAL improvement, in-engine** |
| Continuous regime state (2yr) | net +164p / 3 of 4 at thr=10 | P0 is genuinely unprofitable, not a warm-up artifact |
| Confidence-weighted sizing | doubles net BUT adds leverage/risk | rejected (conflicts with minimize-risk) |
| Session high/low range-fade | 398p gross / 3 of 4 BUT only ~1.4p/trade | **SPREAD TRAP** — gross < 2p spread, loses in reality |

### Key discipline reinforced
A backtest in raw pips can look great yet lose after the ~2-pip round-trip
spread. Any high-frequency edge must clear gross pips-per-trade > spread. The
mean-anchor regime reversion (+$498 through the real engine WITH spread, ~40
trades, ~12+ pips/trade gross) is the genuine result; the high-frequency
range-fade is not.

## Current best (validated, in real engine with spread)
`eurusd_regime_reversion`: ext=22, target_fraction=0.5, stop=12, regime_window=8,
**regime_threshold=5, volume_mult=1.2** → net +$498 over 2yr, positive 3 of 4
periods, worst period −$27. Thin but real, downside-controlled, fixed-risk.

## CRITICAL CORRECTION: the 3-of-4 result was an evaluation artifact

Running the strategy CONTINUOUSLY across 2 years (one regime tracker, as it
would actually deploy) reveals only **1 trade, −$27** — not +$498. The +$498 /
3-of-4 came from evaluating each 6-month period with a FRESH regime tracker,
which gave each period an "innocent until proven" restart.

**Root cause (a real strategy flaw):** the regime gate starves itself. It only
records outcomes from trades it *executes*, but it won't execute when the regime
looks unfavorable — so after one early loss, `strength()` stays negative forever
and it never trades again. The per-period reset hid this deadlock.

**The fix (identified, not yet built):** the regime tracker must learn from
*observed* market reversion outcomes (did each extension revert?), whether or not
we traded it — so the regime read stays live while sitting out. My earlier
from-scratch sim did exactly this and produced the 3-of-4 result; the PRODUCTION
strategy only records executed-trade outcomes, which deadlocks. This requires
feeding observed (counterfactual) outcomes through the runner — a real design
change.

**Honest current state:** the regime-reversion strategy, as actually built and
deployed continuously, does NOT make money. The promising 3-of-4 result is only
achievable IF the observe-every-extension fix is implemented and re-validated
continuously. Until then, no validated profitable strategy exists. The earlier
edge-regime-reversion.md numbers were per-period and are NOT realistic for
continuous deployment.

## FINAL VERDICT on regime-gated reversion: no real edge

Built the fix — the strategy now SELF-OBSERVES every extension's outcome in
evaluate() (whether or not it trades), so the regime tracker stays live and
never deadlocks. Re-ran the honest CONTINUOUS 2-year test:

| threshold | net | %/yr | trades | win | maxDD |
|---|---|---|---|---|---|
| 0 | −$36 | −0.2% | 158 | 44% | $321 |
| 5 | −$106 | −0.5% | 152 | 43% | $377 |
| 10 | −$82 | −0.4% | 141 | 43% | $372 |

With the deadlock fixed and a realistic trade count, the strategy **loses** —
44% win rate, negative net, at every threshold. The earlier +$498/3-of-4 was
entirely the per-period-reset artifact. Marked REJECTED.

## Where the whole search stands

Every avenue — breakout, fade, classic/VWAP/volume/regime reversion, momentum,
gaps, range-fade, other pairs, other sessions, filters, sizing — has been tested
with honest continuous walk-forward validation. **None has a real, deployable
edge on EUR/USD US-open after spread.** The reversion *tendency* is real (~60% at
deep extension) but too weak to clear the ~2-pip spread once you account for
losers and regime shifts. This is consistent with market-efficiency reality:
liquid-FX price-only edges are largely arbitraged away.

The valuable assets produced: a rigorous, honest backtest/walk-forward framework
that repeatedly refused to certify curve-fits, real cached data (multiple
pairs/sessions, 2yr), and documented negative results that save chasing dead
ends. A genuine edge, if one exists, needs information this search did not use:
order-flow/L2 microstructure, the economic calendar, or cross-asset/rates
context — none available from OANDA M5 candles alone.
