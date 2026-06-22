# Strategy Hypotheses

## eurusd_opening_window

- Status: `ready_for_sim`
- Summary: Build a short opening range, then trade a confirmed breakout if spread is acceptable.
- Required inputs: recent candles, current bid/ask quote, spread, session window.
- Risk concerns: false breakouts, spread spikes, stop too tight, news events.

## eurusd_mean_reversion

- Status: `draft`
- Summary: Fade an overextended move back toward a short-term average.
- Required inputs: recent candles, volatility estimate, trend filter.
- Risk concerns: strong trend continuation can overwhelm mean reversion.

## eurusd_news_avoidance

- Status: `draft`
- Summary: Block new trades around known high-impact macro events.
- Required inputs: economic calendar, event severity, session state.
- Risk concerns: event feeds may be incomplete or delayed.

