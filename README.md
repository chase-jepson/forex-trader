# Forex Trader

Forex Trader is a local-first `EUR/USD` trading research and simulation system. It is built to learn safely before it ever talks to a live broker: first-principles notes, deterministic strategy rules, hard risk checks, simulated execution, trade reviews, and reporting all come before OANDA practice mode.

## Modes

- `simulated`: uses an in-memory broker and fake fills. This is the default.
- `practice`: uses broker demo credentials after the simulator is useful and reviewable.
- `live`: intentionally disabled unless explicit safety gates are complete.

## Safety Philosophy

- The LLM can explain trades and summarize reviews, but it cannot place orders or change rules.
- Every trade plan must pass the risk engine before the broker adapter sees it.
- Every trade and blocked trade should produce a review record.
- Default risk is `0.25%` of equity per trade.
- `EUR/USD` is the only v1 instrument.

## Local Commands

```bash
python3.13 -m pytest -v
python3.13 -m streamlit run src/forex_trader/dashboard/app.py
```

Install optional dashboard dependencies from `pyproject.toml` before running Streamlit.

