from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

PRAGMAS = (
    "pragma journal_mode=WAL",
    "pragma foreign_keys=ON",
    "pragma busy_timeout=5000",
    "pragma synchronous=FULL",
    "pragma wal_autocheckpoint=1000",
)

def open_sqlite(path: Path, migrations_package: str) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    for pragma in PRAGMAS:
        connection.execute(pragma)
    from .migrations import apply_migrations
    apply_migrations(connection, migrations_package)
    return connection

@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    connection.execute("begin immediate")
    try:
        yield connection
    except BaseException:
        connection.rollback()
        raise
    else:
        connection.commit()

def quick_check(connection: sqlite3.Connection) -> str:
    result = connection.execute("pragma quick_check").fetchone()[0]
    if result != "ok":
        raise sqlite3.DatabaseError(f"sqlite quick_check failed: {result}")
    return result

def checkpoint_wal(connection: sqlite3.Connection, mode: str = "PASSIVE") -> tuple[int, int, int]:
    if mode not in {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}:
        raise ValueError("invalid WAL checkpoint mode")
    row = connection.execute(f"pragma wal_checkpoint({mode})").fetchone()
    return tuple(row)  # type: ignore[return-value]
