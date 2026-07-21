import asyncio
from datetime import datetime, timezone
from pathlib import Path

from safe_kiosk_people_agent.domain import NewObservationSummary, ProtocolThresholds, Source, StoredObservationSummary
from safe_kiosk_people_agent.metrics import MetricsWorker
from safe_kiosk_people_agent.metrics.service import MetricsService
from safe_kiosk_people_agent.storage.metrics import MetricsStore


def test_service_commits_staged_event_and_reduction(tmp_path: Path) -> None:
    at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    summary = NewObservationSummary("summary-1", Source.WIFI, "run", "token", at, at, at, at, 1, -50, -50, None, None)
    stored = StoredObservationSummary(*summary.__dict__.values(), 1)
    worker = MetricsWorker({Source.WIFI: ProtocolThresholds(Source.WIFI, -55, -80, 1), Source.BLE: ProtocolThresholds(Source.BLE, -60, -85, 1)})
    store = MetricsStore(tmp_path / "metrics.sqlite")
    service = MetricsService(worker, lambda: [stored], clock=lambda: at.replace(minute=10), store=store)
    asyncio.run(service.run_once(at.replace(minute=10)))
    assert store.db.execute("select count(*) from metric_event").fetchone()[0] == 1
    assert store.db.execute("select consumed from metric_event").fetchone()[0] == 1
