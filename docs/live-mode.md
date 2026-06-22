# Live Practice Mode — Operating Guide

This describes how to run the trading loop against an OANDA **practice** account.
Live (real-money) mode shares the same machinery but is disabled by default and
out of scope until practice has produced reviewed evidence.

> **The loop is built and tested but is never started automatically.** Arming it
> and running it against the account is a deliberate human action.

## Safety model

Every tick, in order:

1. **Emergency stop** — if the stop file exists (`EMERGENCY_STOP_PATH`, default
   `STOP_TRADING`), the tick halts and places nothing. Trip it any time with
   `trip_emergency_stop` or by creating the file.
2. **Reconciliation** — broker-reported open positions are compared to local
   state. On mismatch the tick returns `out_of_sync` and places nothing.
3. **Dry run vs armed** — without `--arm`, the loop evaluates signals and logs
   intended actions but never reaches the risk engine or broker. With `--arm`
   (plus acknowledgement), orders flow through the **same risk engine** as
   simulation — there is no bypass.

The `live` command refuses to start unless:

- `APP_MODE` is `practice` or `live`
- `OANDA_ACCOUNT_ID` and `OANDA_API_TOKEN` are present
- `ENABLE_LIVE_TRADING=true` (only required for `live`)
- `--arm` is paired with `--i-understand-this-places-orders`

## Pre-flight checklist

- [ ] `.env` has practice credentials; `APP_MODE=practice`
- [ ] `forex-trader status` reports the expected mode and a passing startup
- [ ] OANDA health check passes (`OandaBroker.health_check()`)
- [ ] You have reviewed backtest/evidence output and accept the strategy
- [ ] Emergency-stop path is known and writable

## Running

Dry run (safe — no orders, logs intended actions):

```bash
forex-trader live --max-iterations 5
```

Armed against the **practice** account (places demo orders):

```bash
APP_MODE=practice forex-trader live --arm --i-understand-this-places-orders \
  --max-iterations 10 --sleep-seconds 60
```

To halt immediately, create the stop file:

```bash
touch STOP_TRADING
```

## What is intentionally NOT automated

- The agent never runs `--arm` on your behalf.
- Promoting a draft strategy to `ready_for_sim` is a research decision.
- Real-money `live` mode requires the explicit gates above and reviewed
  practice evidence first.
