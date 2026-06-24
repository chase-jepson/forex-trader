# Conclusion: No Stable Simple-Rule Edge (EUR/USD US-open)

This documents the honest result of an exhaustive search for a profitable
deterministic rule on EUR/USD during the US-open window (08:30–11:30 ET), using
6 and 12 months of real OANDA data with strict walk-forward validation.

## What was tested

| Idea | Result (walk-forward / both-halves of 12mo) |
|---|---|
| Opening-range **breakout** | Loses; ~37% win even optimized |
| **Fade** the opening-range thrust | Loses; small wins don't cover trend days |
| Classic **mean reversion** (SMA) | No config positive in both halves |
| **Session-mean (VWAP) reversion** | Looked good on 6mo, FAILED on 12mo (regime artifact) |
| **Trend / momentum following** | 47–49% continuation — no edge |
| **Overnight gap** follow/fade | 47% follow — no edge |
| Trend filter, volatility-regime filter | Reduce losses, create no edge |

**Zero** strategy configurations across the whole family are profitable in both
halves of the 12-month set.

## Why: the window is directionally efficient

Every directional predictor measured sits at **~47–49%** — statistically
indistinguishable from (and slightly worse than) a coin flip after the spread:

- First-30-min direction → rest of session: **47.7%**
- 5-min candle momentum continuation: **47.4–48.8%**
- Overnight gap → session direction: **47%**

There is a *weak* mean-reversion tendency (price stretched far from the session
mean reverts ~60% short-term), but it is **not stable across regimes** — it paid
in the recent 6 months and lost in the prior 6. After the ~1–2 pip spread, the
weak bias does not survive.

## The honest bottom line

Simple price-pattern rules do **not** have a durable edge on EUR/USD in this
window. This is consistent with market-efficiency research: liquid FX majors
rarely yield to retail-accessible price-only rules. The walk-forward framework
did its job — it repeatedly refused to certify a curve-fit.

## Where a real edge would have to come from (not yet attempted)

A durable edge, if one exists, likely needs information beyond price-in-a-window:

1. **Regime adaptation** — detect trending vs ranging days and switch rules,
   validated so the switch itself isn't curve-fit.
2. **External signal** — economic-calendar timing (trade/avoid around releases),
   rate-differential or cross-asset context.
3. **Microstructure** — actual tick volume / order-flow (OANDA M5 has volume we
   are not yet using), spread dynamics.
4. **Different instrument/timeframe** — some pairs/sessions are less efficient.

Each is a real experiment the existing framework can validate the same rigorous
way. None should be deployed on the strength of one 6-month sample again.
