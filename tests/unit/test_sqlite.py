import sqlite3
from pathlib import Path
from safe_kiosk_people_agent.storage.sqlite import open_sqlite, quick_check

def test_open_sqlite_enforces_durability(tmp_path: Path) -> None:
    db = open_sqlite(tmp_path / "metrics.sqlite", "safe_kiosk_people_agent.storage.schema.metrics")
    assert db.execute("pragma journal_mode").fetchone()[0] == "wal"
    assert db.execute("pragma foreign_keys").fetchone()[0] == 1
    assert db.execute("pragma synchronous").fetchone()[0] == 2
    assert db.execute("pragma busy_timeout").fetchone()[0] == 5000
    assert quick_check(db) == "ok"

def test_metric_event_rejects_duplicate_summary(tmp_path: Path) -> None:
    db = open_sqlite(tmp_path / "metrics.sqlite", "safe_kiosk_people_agent.storage.schema.metrics")
    row = ("wifi", "same", 1, "2026-07-14T00:00:00Z", "{}")
    db.execute("insert into metric_event(source,summary_id,spool_sequence,event_time,payload_json) values(?,?,?,?,?)", row)
    try:
        with __import__("pytest").raises(sqlite3.IntegrityError):
            db.execute("insert into metric_event(source,summary_id,spool_sequence,event_time,payload_json) values(?,?,?,?,?)", row)
    finally: db.close()
