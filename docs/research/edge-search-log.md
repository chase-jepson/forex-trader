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
