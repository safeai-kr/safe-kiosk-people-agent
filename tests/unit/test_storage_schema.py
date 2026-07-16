from pathlib import Path
from safe_kiosk_people_agent.storage.sqlite import open_sqlite, quick_check

def test_all_schema_fixtures_are_integrity_checked(tmp_path: Path) -> None:
    for name in ("wifi", "ble", "metrics"):
        db = open_sqlite(tmp_path / f"{name}.sqlite", f"safe_kiosk_people_agent.storage.schema.{name}")
        assert quick_check(db) == "ok"
        assert db.execute("select count(*) from schema_version").fetchone()[0] == 1
        db.close()

def test_metrics_constraints(tmp_path: Path) -> None:
    db = open_sqlite(tmp_path / "metrics.sqlite", "safe_kiosk_people_agent.storage.schema.metrics")
    import sqlite3
    with __import__("pytest").raises(sqlite3.IntegrityError):
        db.execute("insert into bucket_metric values('2026-01-01','2026-01-01','{}',-1,0,0)")
