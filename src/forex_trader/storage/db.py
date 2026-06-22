from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def connect(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection, commit on success, and always close it.

    Using this as a context manager prevents file-descriptor leaks under
    high-frequency loops (backtests open one connection per persisted row).
    """
    path = Path(database_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
