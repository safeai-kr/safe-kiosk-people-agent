from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from ..domain import SensorStatus, SourceHealth, UploadRunResult
from .contracts import build_ingest_request


def _empty_status(now: datetime) -> SensorStatus:
    return SensorStatus(now, SourceHealth.HEALTHY, SourceHealth.HEALTHY, SourceHealth.HEALTHY, SourceHealth.HEALTHY, SourceHealth.HEALTHY, None, None, None, None, {}, Decimal(0), 0, 0, 0, None, "manual", "metric-v1")


class Uploader:
    def __init__(self, store, client, *, sensor_id: UUID | None = None, status_provider=None, batch_size: int = 288):
        self.store = store
        self.client = client
        self.sensor_id = sensor_id or UUID(int=0)
        self.status_provider = status_provider or _empty_status
        self.batch_size = min(batch_size, 288)

    async def run_once(self, now: datetime) -> UploadRunResult:
        rows = self.store.claim_ready(now, limit=self.batch_size)
        metrics = [row.metric for row in rows]
        try:
            request = build_ingest_request(self.sensor_id, self.status_provider(now), metrics)
            response = await self.client.post(request)
        except Exception:
            return UploadRunResult(0, (), (), bool(rows), False, not bool(rows))
        delivered: list[datetime] = []
        terminal: list[datetime] = []
        for result in response.get("metrics", []):
            index = int(result["index"])
            if index >= len(rows):
                continue
            row = rows[index]
            bucket = datetime.fromisoformat(row.bucket_start)
            if self.store.apply_server_result(row.bucket_start, row.revision, result["result"]):
                if result["result"] == "rejected":
                    terminal.append(bucket)
                else:
                    delivered.append(bucket)
        return UploadRunResult(len(delivered), tuple(delivered), tuple(terminal), False, False, not bool(rows))

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            await self.run_once(datetime.now(timezone.utc))
            try:
                await asyncio.wait_for(stop.wait(), 300)
            except asyncio.TimeoutError:
                pass

    async def run_resilient(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await self.run(stop)
            except Exception:
                await asyncio.sleep(10)


# Compatibility name for callers that imported the old service result.
UploadRun = UploadRunResult
