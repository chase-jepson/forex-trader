# Findings: US-Open Window Analysis (real EUR/USD, 6 months)

Generated from `forex-trader analyze --months 6` over 4,699 real M5 candles in
the 08:30–11:30 ET window across 127 trading days.

## Headline

The opening-window **breakout** strategy has **no edge** here — and that's a
rigorously validated result, not a hunch:

| | In-sample (optimized) | Out-of-sample (validated) |
|---|---|---|
| PnL | -$890 | -$1,116 |
| Win rate | 37.2% | 32.6% |
| Expectancy | -$3.68/trade | -$4.73/trade |

Even the **best** parameters found by grid search lose on both halves. Not
overfit — consistently negative. Tuning cannot save this rule.

## Why it loses (the key insight)

- **Breakout follow-through rate: 46.6%.** When price breaks the prior candle's
  high, it continues higher less than half the time. The breakout strategy bets
  on continuation, but this window **mean-reverts after breakouts**. The rule is
  backwards relative to the data.
- **Up-day rate 45.7%, slight downward drift.** No strong directional edge.
- **Avg range 5.66 pips/M5** — modest volatility; the ~1–2 pip spread is a real
  drag on a strategy that trades often.

## Evidence-based rule hypothesis (for review, NOT auto-deployed)

The 46.6% follow-through rate points the other way: **fade** the breakout rather
than chase it. A mean-reversion entry — sell a thrust above the opening range,
buy a thrust below, targeting the range mid — is the hypothesis the data
actually supports. This is scaffolded as a **draft** strategy
(`eurusd_us_open_fade`), gated behind the research registry; it must be
backtested + walk-forward validated before it is ever marked `ready_for_sim`.

## Honest caveat

A 46.6% follow-through doesn't guarantee a fade is profitable — after spread and
the occasional strong trend day, fades can bleed too. The next step is to run
the same walk-forward on the fade rule and let the out-of-sample result decide.
No edge is assumed until validated.

## UPDATE: fade strategy validated — also loses

Ran the same walk-forward on the draft fade strategy:

| thrust | in-sample | out-of-sample |
|---|---|---|
| 8 pips | -$219 (22% win) | -$918 (23% win) |
| 12 pips | -$387 (14% win) | -$855 (19% win) |

The mean-reversion direction was *better aligned* with the data than the
breakout, but a naive fade still loses after spread — the small wins (target =
range mid) don't cover the losers when a strong trend day runs the stop. The
fade remains DRAFT/rejected as a standalone rule.

**Conclusion: neither naive direction (breakout or fade) has an edge on real
EUR/USD in the US-open window.** A profitable rule, if one exists here, needs
something more than price-thrust direction — e.g. a volatility/regime filter, a
trend filter to skip trend days, news-event avoidance, or a different target
logic. The framework is ready to test any of these the same rigorous way.
