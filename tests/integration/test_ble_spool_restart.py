from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event

from safe_kiosk_people_agent.ble import BleAdvertisement, BleCollectorWorker, BleObservationCollector
from safe_kiosk_people_agent.domain import Source
from safe_kiosk_people_agent.privacy import DeviceTokenizer
from safe_kiosk_people_agent.storage.spool import BleSpool


def test_ble_worker_persists_summaries_and_progress(tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    now = [start + timedelta(seconds=11)]
    spool = BleSpool(tmp_path / "ble.sqlite")
    worker = BleCollectorWorker(
        BleObservationCollector(DeviceTokenizer(b"x" * 32), "run"),
        lambda: [BleAdvertisement("aa:bb:cc:dd:ee:ff", -50, start)],
        clock=lambda: now[0],
        spool=spool,
    )
    result = worker.run(Event(), max_cycles=1)
    assert result.health.value == "healthy"
    assert len(spool.read_after(0, 10)) == 1
    watermark = spool.read_watermark()
    assert watermark is not None and watermark.progress_sequence == 1
    assert watermark.source is Source.BLE
