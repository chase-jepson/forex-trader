from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from forex_trader.domain.models import PIP_SIZE, Candle


def load_candles_csv(path: str | Path) -> list[Candle]:
    """Load OHLC candles from a CSV with columns: time, open, high, low, close.

    `time` must be ISO-8601 (e.g. 2026-06-22T12:00:00+00:00).
    """
    candles: list[Candle] = []
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"time", "open", "high", "low", "close"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain columns {sorted(required)}.")
        for row in reader:
            candles.append(
                Candle(
                    time=datetime.fromisoformat(row["time"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                )
            )
    return candles


def generate_synthetic_candles(
    *,
    start: datetime,
    count: int,
    seed: int = 0,
    start_price: float = 1.1000,
    step_minutes: int = 1,
    volatility_pips: float = 3.0,
) -> list[Candle]:
    """Generate a deterministic seeded random-walk candle series.

    Used for backtests and dashboard demos when no historical CSV is supplied.
    The same seed always yields the same series so results are reproducible.
    """
    rng = random.Random(seed)
    vol = volatility_pips * PIP_SIZE
    candles: list[Candle] = []
    price = start_price
    for index in range(count):
        drift = rng.uniform(-vol, vol)
        open_price = price
        close_price = max(0.0001, open_price + drift)
        # Wicks extend a fraction of a candle's body beyond open/close.
        wick = abs(rng.uniform(0, vol))
        high = max(open_price, close_price) + wick
        low = min(open_price, close_price) - wick
        candles.append(
            Candle(
                time=start + timedelta(minutes=step_minutes * index),
                open=round(open_price, 5),
                high=round(high, 5),
                low=round(low, 5),
                close=round(close_price, 5),
            )
        )
        price = close_price
    return candles
