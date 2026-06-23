# Walk-Forward Analysis (US-open window)

Window: 08:30-11:30 ET, M5, ~6 months (4699 session candles).

## Market stats (whole window)

```json
{
  "candle_count": 4699,
  "day_count": 127,
  "avg_range_pips": 5.66,
  "net_move_pips": -411.4,
  "directional_bias": "down",
  "up_day_rate": 0.457,
  "breakout_follow_through_rate": 0.466
}
```

## Walk-forward result

```json
{
  "best_params": {
    "reward_to_risk": 2.5,
    "max_spread_pips": 2.0
  },
  "split_date": "2026-03-26T02:30:00+00:00",
  "in_sample": {
    "pnl": -890.24,
    "win_rate": 0.3719,
    "expectancy": -3.68,
    "trades": 242,
    "max_drawdown": 986.01
  },
  "out_of_sample": {
    "pnl": -1115.8,
    "win_rate": 0.3263,
    "expectancy": -4.73,
    "trades": 236,
    "max_drawdown": 1478.2
  },
  "looks_overfit": false
}
```
