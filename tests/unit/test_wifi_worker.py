import sqlite3
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from safe_kiosk_people_agent.domain import KismetGeneration
from safe_kiosk_people_agent.kismet.reader import KismetReader
from safe_kiosk_people_agent.privacy import DeviceTokenizer
from safe_kiosk_people_agent.storage.spool import WifiSpool
from safe_kiosk_people_agent.wifi.collector import WifiObservationCollector
from safe_kiosk_people_agent.wifi.worker import WifiCollectorWorker


import pytest


@pytest.mark.asyncio
async def test_wifi_worker_commits_cursor_and_tokenized_summary(tmp_path: Path) -> None:
    db_path = tmp_path / "kismet.db"
    db = sqlite3.connect(db_path)
    db.execute("create table packets (ts_sec integer, ts_usec integer, sourcemac text, signal_dbm integer, frequency integer, tags text)")
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    db.execute("insert into packets values (?, ?, ?, ?, ?, ?)", (int(start.timestamp()), 0, "aa:bb:cc:dd:ee:ff", -50, 2412_000, "DOT11_PROBE_REQ"))
    db.commit(); db.close()
    generation = KismetGeneration("g1", db_path, "active", "boot", None, None, None, start, None, None)
    manager = type("Generations", (), {"current": generation})()
    spool = WifiSpool(tmp_path / "wifi.sqlite")
    now = [start + timedelta(seconds=11)]
    worker = WifiCollectorWorker(WifiObservationCollector(DeviceTokenizer(b"x" * 32), "run"), KismetReader(db_path), manager, spool, clock=lambda: now[0])
    result = await worker.run(asyncio.Event(), max_cycles=1)
    assert result.health.value == "healthy"
    assert len(spool.read_after(0, 10)) == 1
    assert spool.read_cursor("g1") is not None
    assert b"aa:bb:cc:dd:ee:ff" not in b"".join(str(row).encode() for row in spool.read_after(0, 10))
