# Trade Explorer + Tuning + Hardening — Work Plan

Building while user is away. All non-transacting. Commit per chunk, push, keep green.

## Centerpiece: Trade Explorer (click a trade → see the story)

The user wants: click a trade the agent made → see the chart + what it was
tracking pre-entry that made it expect success → follow it through to close.

### Data backbone (persist the story)
- [ ] T1: Persist richer trade lifecycle. Each trade gets: pre-entry candle
      window, the signal (side/entry/stop/target/reason/metadata), risk
      decision, and the exit (price, time, outcome, pnl). New `trades` table
      or enrich cycle payloads. TDD on the repository.
- [ ] T2: Persist dry-run observations too — every dry-run signal + market
      context recorded as a "would-have-traded" record, so evidence accrues
      safely without placing orders.
- [ ] T3: A TradeStory builder: given a trade id, assemble candles-before +
      entry marker + stop/target lines + exit marker into one view model.

### Visualization (Streamlit + Plotly)
- [ ] T4: Plotly candlestick helper with entry/stop/target/exit markers.
- [ ] T5: Trade Explorer page: a clickable trade list (selectbox) → renders the
      candlestick chart for the selected trade with the signal reasoning, risk
      decision, and lifecycle annotations.
- [ ] T6: Wire the page into the dashboard app; seed demo data so it's
      viewable immediately.

## Tune strategies
- [ ] S1: Fix mean-reversion taking 0 trades (loosen lookback/deviation to
      realistic values; verify it trades on real-ish data).
- [ ] S2: Make strategy params configurable so the evidence comparison is fair.

## Polish & harden
- [ ] H1: Expand live-loop test coverage (out_of_sync path, health fail path).
- [ ] H2: Bug-hunt / simplification sweep.
- [ ] H3: Docs: how to view the dashboard, trade-explorer guide.

## Verify every chunk: pytest -q, ruff, mypy strict. Commit + push.
