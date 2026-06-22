from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forex_trader.storage.db import connect


class TradingRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = database_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with connect(self.database_path) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS cycles (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    id TEXT PRIMARY KEY,
                    trade_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            # Single-row table holding the live loop's resumable state.
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS run_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_tick TEXT NOT NULL,
                    current_day TEXT NOT NULL,
                    daily_realized_pnl REAL NOT NULL,
                    cumulative_realized_pnl REAL NOT NULL
                )
                """
            )

    def save_run_state(
        self,
        *,
        last_tick: str,
        current_day: str,
        daily_realized_pnl: float,
        cumulative_realized_pnl: float,
    ) -> None:
        with connect(self.database_path) as db:
            db.execute(
                """
                INSERT INTO run_state
                    (id, last_tick, current_day, daily_realized_pnl, cumulative_realized_pnl)
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    last_tick = excluded.last_tick,
                    current_day = excluded.current_day,
                    daily_realized_pnl = excluded.daily_realized_pnl,
                    cumulative_realized_pnl = excluded.cumulative_realized_pnl
                """,
                (last_tick, current_day, daily_realized_pnl, cumulative_realized_pnl),
            )

    def load_run_state(self) -> dict[str, Any] | None:
        with connect(self.database_path) as db:
            row = db.execute("SELECT * FROM run_state WHERE id = 1").fetchone()
        if row is None:
            return None
        return {
            "last_tick": row["last_tick"],
            "current_day": row["current_day"],
            "daily_realized_pnl": row["daily_realized_pnl"],
            "cumulative_realized_pnl": row["cumulative_realized_pnl"],
        }

    def save_cycle(
        self,
        cycle_id: str,
        created_at: str,
        status: str,
        reason: str,
        payload: dict[str, Any],
    ) -> None:
        with connect(self.database_path) as db:
            db.execute(
                """
                INSERT INTO cycles (id, created_at, status, reason, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (cycle_id, created_at, status, reason, json.dumps(payload, default=str)),
            )

    def list_cycles(self) -> list[dict[str, Any]]:
        with connect(self.database_path) as db:
            rows = db.execute("SELECT * FROM cycles ORDER BY created_at").fetchall()
        return [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "status": row["status"],
                "reason": row["reason"],
                **json.loads(row["payload"]),
            }
            for row in rows
        ]

    def save_review(
        self,
        review_id: str,
        trade_id: str,
        outcome: str,
        payload: dict[str, Any],
    ) -> None:
        with connect(self.database_path) as db:
            db.execute(
                "INSERT INTO reviews (id, trade_id, outcome, payload) VALUES (?, ?, ?, ?)",
                (review_id, trade_id, outcome, json.dumps(payload, default=str)),
            )

    def list_reviews(self) -> list[dict[str, Any]]:
        with connect(self.database_path) as db:
            rows = db.execute("SELECT * FROM reviews ORDER BY id").fetchall()
        return [
            {
                "id": row["id"],
                "trade_id": row["trade_id"],
                "outcome": row["outcome"],
                **json.loads(row["payload"]),
            }
            for row in rows
        ]
