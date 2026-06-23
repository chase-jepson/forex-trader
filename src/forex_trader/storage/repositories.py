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
            # One row per trade holding the full lifecycle story for the
            # trade explorer: the candles the strategy saw before entry, the
            # signal reasoning, the risk decision, and the eventual exit.
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    position_id TEXT PRIMARY KEY,
                    opened_at TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    units INTEGER NOT NULL,
                    signal_reason TEXT NOT NULL,
                    signal_metadata TEXT NOT NULL,
                    risk_reason TEXT NOT NULL,
                    context_candles TEXT NOT NULL,
                    is_dry_run INTEGER NOT NULL DEFAULT 0,
                    closed_at TEXT,
                    close_price REAL,
                    outcome TEXT NOT NULL DEFAULT 'open',
                    pnl REAL,
                    exit_reason TEXT
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

    def open_trade_story(
        self,
        *,
        position_id: str,
        opened_at: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        units: int,
        signal_reason: str,
        signal_metadata: dict[str, Any],
        risk_reason: str,
        context_candles: list[dict[str, Any]],
        is_dry_run: bool = False,
    ) -> None:
        with connect(self.database_path) as db:
            db.execute(
                """
                INSERT OR REPLACE INTO trades (
                    position_id, opened_at, side, entry_price, stop_loss,
                    take_profit, units, signal_reason, signal_metadata,
                    risk_reason, context_candles, is_dry_run, outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
                """,
                (
                    position_id, opened_at, side, entry_price, stop_loss,
                    take_profit, units, signal_reason,
                    json.dumps(signal_metadata, default=str), risk_reason,
                    json.dumps(context_candles, default=str), int(is_dry_run),
                ),
            )

    def close_trade_story(
        self,
        *,
        position_id: str,
        closed_at: str,
        close_price: float,
        outcome: str,
        pnl: float,
        exit_reason: str,
    ) -> None:
        with connect(self.database_path) as db:
            db.execute(
                """
                UPDATE trades
                SET closed_at = ?, close_price = ?, outcome = ?, pnl = ?,
                    exit_reason = ?
                WHERE position_id = ?
                """,
                (closed_at, close_price, outcome, pnl, exit_reason, position_id),
            )

    def clear_all(self) -> None:
        """Delete all cycles, reviews, and trade stories. Used by `seed` to
        start from a clean slate so the dashboard is not double-populated."""
        with connect(self.database_path) as db:
            db.execute("DELETE FROM cycles")
            db.execute("DELETE FROM reviews")
            db.execute("DELETE FROM trades")

    def update_story_candles(
        self, position_id: str, context_candles: list[dict[str, Any]]
    ) -> None:
        with connect(self.database_path) as db:
            db.execute(
                "UPDATE trades SET context_candles = ? WHERE position_id = ?",
                (json.dumps(context_candles, default=str), position_id),
            )

    def get_trade_story(self, position_id: str) -> dict[str, Any] | None:
        with connect(self.database_path) as db:
            row = db.execute(
                "SELECT * FROM trades WHERE position_id = ?", (position_id,)
            ).fetchone()
        return None if row is None else self._row_to_story(row)

    def list_trade_stories(self) -> list[dict[str, Any]]:
        with connect(self.database_path) as db:
            rows = db.execute("SELECT * FROM trades ORDER BY opened_at").fetchall()
        return [self._row_to_story(row) for row in rows]

    @staticmethod
    def _row_to_story(row: Any) -> dict[str, Any]:
        return {
            "position_id": row["position_id"],
            "opened_at": row["opened_at"],
            "side": row["side"],
            "entry_price": row["entry_price"],
            "stop_loss": row["stop_loss"],
            "take_profit": row["take_profit"],
            "units": row["units"],
            "signal_reason": row["signal_reason"],
            "signal_metadata": json.loads(row["signal_metadata"]),
            "risk_reason": row["risk_reason"],
            "context_candles": json.loads(row["context_candles"]),
            "is_dry_run": bool(row["is_dry_run"]),
            "closed_at": row["closed_at"],
            "close_price": row["close_price"],
            "outcome": row["outcome"],
            "pnl": row["pnl"],
            "exit_reason": row["exit_reason"],
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
