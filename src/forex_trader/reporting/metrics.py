from __future__ import annotations

from collections import Counter
from typing import Any


def summarize_trade_outcomes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if row.get("outcome") in {"win", "loss", "scratch"}]
    wins = sum(1 for row in closed if row.get("outcome") == "win")
    losses = sum(1 for row in closed if row.get("outcome") == "loss")
    realized_pnl = sum(float(row.get("pnl", 0.0)) for row in closed)
    hold_times = [float(row["hold_minutes"]) for row in closed if "hold_minutes" in row]
    blocked_reasons = Counter(
        str(row.get("reason", "unknown")) for row in rows if row.get("outcome") == "blocked"
    )
    denominator = wins + losses
    return {
        "total_rows": len(rows),
        "trades_closed": len(closed),
        "trades_blocked": sum(1 for row in rows if row.get("outcome") == "blocked"),
        "win_rate": 0.0 if denominator == 0 else wins / denominator,
        "realized_pnl": realized_pnl,
        "average_hold_minutes": 0.0 if not hold_times else sum(hold_times) / len(hold_times),
        "top_blocked_reasons": blocked_reasons.most_common(),
    }

