import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from safe_kiosk_people_agent.domain import BucketMetric, ProtocolSourceDetail, Source
from safe_kiosk_people_agent.storage.outbox import OutboxStore
from safe_kiosk_people_agent.upload.service import Uploader


def metric() -> BucketMetric:
    at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return BucketMetric(at, at.replace(minute=5), 1, 1, 1, 1, Decimal(60), Decimal(1), 1, 1, Decimal("1"), (), {Source.WIFI: ProtocolSourceDetail(1, 1, 1, Decimal(60), Decimal(1), 0, 0, 0), Source.BLE: ProtocolSourceDetail(1, 0, 0, Decimal(0), Decimal(0), 0, 0, 0)}, "threshold-v1", "metric-v1", 1, at)


class Client:
    async def post(self, request):
        return {"metrics": [{"index": 0, "result": "inserted"}], "status_result": "inserted"}


def test_upload_backfill_reconstructs_typed_metric(tmp_path: Path) -> None:
    store = OutboxStore(tmp_path / "metrics.sqlite")
    store.upsert(metric())
    result = asyncio.run(Uploader(store, Client()).run_once(datetime.now(timezone.utc)))
    assert result.metrics_sent == 1
    assert store.pending_count() == 0
