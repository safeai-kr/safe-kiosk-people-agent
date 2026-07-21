from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Callable, Iterable

from ..domain import (
    BucketMetric,
    MetricsRunResult,
    ProtocolSourceDetail,
    SensorStatus,
    Source,
    SourceHealth,
    NewObservationSummary,
    StoredObservationSummary,
    ReductionBatch,
    SourceCursor,
    ScheduledAction,
    StateSnapshot,
)
from .fusion import build_bucket_metric
from .replay import ReplayEngine
from .worker import MetricsWorker


class MetricsService:
    """Event-time scheduler boundary with deterministic bucket fusion."""

    def __init__(self, worker: MetricsWorker, supplier: Callable[[], Iterable] = lambda: (), *, uploader=None, clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc), store=None, replay_engine: ReplayEngine | None = None):
        self.worker = worker
        self.supplier = supplier
        self.uploader = uploader
        self.clock = clock
        self.health = {Source.WIFI: SourceHealth.HEALTHY, Source.BLE: SourceHealth.HEALTHY}
        self._health_events: list[tuple[Source, SourceHealth, datetime]] = []
        self._pending: list[NewObservationSummary] = []
        self._revision: dict[datetime, int] = {}
        self.store = store
        self.replay_engine = replay_engine or ReplayEngine()
        self._processed_through: datetime | None = None

    def record_health(self, source: Source, health: SourceHealth, at: datetime) -> None:
        at = at.astimezone(timezone.utc)
        self.health[source] = health
        self._health_events.append((source, health, at))

    def _status(self, now: datetime) -> SensorStatus:
        return SensorStatus(now, SourceHealth.HEALTHY, self.health[Source.WIFI], self.health[Source.BLE], SourceHealth.HEALTHY, SourceHealth.HEALTHY, None, None, None, None, {}, Decimal(0), 0, 0, 0, None, "manual", "metric-v1")

    async def run_once(self, now: datetime | None = None) -> MetricsRunResult:
        current = (now or self.clock()).astimezone(timezone.utc)
        values = list(self.supplier())
        self._pending.extend(values)
        reduced = self.worker.reduce(self._pending)
        self._pending.clear()
        quality = tuple(f"{source.value}_unavailable" for source, state in self.health.items() if state is SourceHealth.UNAVAILABLE)
        closed: list[BucketMetric] = []
        for bucket in reduced:
            if bucket.bucket_start + timedelta(seconds=330) > current:
                continue
            inside: dict[Source, int | None] = {source: None for source in Source}
            # The legacy reducer has one fused count; retain it for a source when
            # only that source contributed and mark dual-source buckets as both.
            if len(bucket.sources) == 1:
                inside[bucket.sources[0]] = bucket.estimated_people_count
            elif len(bucket.sources) == 2:
                inside = {Source.WIFI: bucket.estimated_people_count, Source.BLE: bucket.estimated_people_count}
            details = {source: ProtocolSourceDetail(30 if inside.get(source) is not None else 0, 0, 0, Decimal(0), Decimal(0), 0, 0, 0) for source in Source}
            revision = self._revision.get(bucket.bucket_start, 0) + 1
            self._revision[bucket.bucket_start] = revision
            counts = {source: bucket.observation_count // len(bucket.sources) for source in bucket.sources}
            if len(bucket.sources) == 1:
                counts[bucket.sources[0]] = bucket.observation_count
            metric = build_bucket_metric(bucket.bucket_start, inside, details, {Source.WIFI: Decimal("1"), Source.BLE: Decimal("1")}, revision=revision, generated_at=current, observation_counts=counts)
            if metric is not None:
                closed.append(metric)
        replay_outcomes = []
        replayed_metrics: list[BucketMetric] = []
        if self.store is not None:
            stored = tuple(value for value in values if isinstance(value, StoredObservationSummary))
            events = self.store.stage_source_rows(stored) if stored else ()
            processed = self._processed_through or current
            late = tuple(event for event in events if event.event_time < processed)
            if late:
                snapshot = self.store.load_runtime_state() or StateSnapshot(current, processed, {}, "{}", 1)
                replay_result = self.replay_engine.rebuild(tuple(ScheduledAction("event", event.event_time, event.source, event.spool_sequence, event) for event in late), processed - timedelta(hours=1), current, snapshot, {})
                replay_outcomes.append(replay_result)
                replayed_metrics.extend(replay_result.rebuilt_buckets)
            cursors = tuple(SourceCursor(event.source, event.summary.collector_run_id, event.spool_sequence, event.event_time) for event in events)
            all_metrics = tuple(closed) + tuple(replayed_metrics)
            outbox = tuple({"bucket_start": metric.bucket_start.isoformat(), "payload_json": __import__("json").dumps(metric.to_wire(), sort_keys=True), "revision": metric.revision} for metric in all_metrics)
            reduction = ReductionBatch((), (), (), all_metrics, (), outbox, cursors, tuple((event.source, event.summary_id) for event in events))
            self.store.commit_reduction(reduction)
        self._processed_through = current
        return MetricsRunResult((), (), tuple(replay_outcomes), tuple(closed) + tuple(replayed_metrics), 0, self._status(current), quality)

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            await self.run_once(self.clock())
            try:
                await asyncio.wait_for(stop.wait(), 10)
            except asyncio.TimeoutError:
                pass


async def run_metrics_service(service: MetricsService, stop: asyncio.Event) -> None:
    tasks = [asyncio.create_task(service.run(stop))]
    if service.uploader is not None:
        tasks.append(asyncio.create_task(service.uploader.run_resilient(stop)))
    await asyncio.gather(*tasks)
