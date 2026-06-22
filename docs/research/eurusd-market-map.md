# EUR/USD Market Map

`EUR/USD` is one of the most liquid forex pairs. It often sees more activity when European and US market participants overlap, but the system must validate its target window with simulated and practice data.

## Initial Window Hypothesis

The v1 simulator targets a configurable morning window in local time. This is not a claim that the window is profitable. It is a controlled learning frame for observing signals, spreads, fills, and exits.

## Risks To Track

- spreads widening around quiet periods or news
- false breakouts after a narrow range
- stops set too tightly for normal noise
- holding too long after the original setup is gone
- strategy behavior changing around holidays or low-liquidity sessions

