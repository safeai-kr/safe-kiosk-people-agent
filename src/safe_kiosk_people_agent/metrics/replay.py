from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Mapping, Sequence

from ..clock import floor_utc
from ..domain import (
    BucketMetric,
    ConfigSnapshot,
    LateQuarantineRecord,
    MetricEvent,
    ProtocolSourceDetail,
    ReplayResult,
    ScheduledAction,
    Source,
    StateSnapshot,
)
from .fusion import build_bucket_metric


class ReplayEngine:
    def __init__(self) -> None:
        self._revisions: dict[datetime, int] = {}
        self._fingerprints: dict[datetime, str] = {}

    def _rebuild_bucket(self, bucket_start: datetime, events: Sequence[MetricEvent]) -> BucketMetric:
        tokens: dict[Source, set[str]] = {Source.WIFI: set(), Source.BLE: set()}
        observations: dict[Source, int] = {Source.WIFI: 0, Source.BLE: 0}
        for event in events:
            source = event.source
            observations[source] += event.summary.sample_count
            if event.summary.median_rssi_dbm >= -70:
                tokens[source].add(event.summary.device_token)
        inside = {source: len(tokens[source]) for source in Source}
        details = {
            source: ProtocolSourceDetail(inside[source], 0, 0, Decimal(0), Decimal(0), 0, 0, 0)
            for source in Source
        }
        payload = json.dumps([(event.source.value, event.summary_id, event.spool_sequence, event.summary.median_rssi_dbm) for event in events], sort_keys=True)
        fingerprint = hashlib.sha256(payload.encode()).hexdigest()
        revision = self._revisions.get(bucket_start, 0)
        if self._fingerprints.get(bucket_start) != fingerprint:
            revision += 1
            self._revisions[bucket_start] = revision
            self._fingerprints[bucket_start] = fingerprint
        metric = build_bucket_metric(
            bucket_start,
            inside,
            details,
            {Source.WIFI: Decimal("1"), Source.BLE: Decimal("1")},
            revision=max(1, revision),
            observation_counts=observations,
        )
        if metric is None:
            raise RuntimeError("replay bucket unexpectedly unavailable")
        return metric

    def rebuild(
        self,
        actions: Sequence[ScheduledAction],
        window_start: datetime,
        window_end: datetime,
        snapshot: StateSnapshot,
        config_snapshots: Mapping[int, ConfigSnapshot],
    ) -> ReplayResult:
        if window_start.tzinfo is None or window_end.tzinfo is None:
            raise ValueError("replay window must be timezone-aware")
        now = datetime.now(timezone.utc)
        ordered = tuple(sorted(actions, key=lambda action: (action.at, action.kind, action.source.value if action.source else "", action.spool_sequence)))
        events = tuple(action.payload for action in ordered if action.kind == "event" and isinstance(action.payload, MetricEvent))
        payload_metrics = tuple(action.payload for action in ordered if action.kind == "event" and isinstance(action.payload, BucketMetric))
        if window_start < now - timedelta(hours=24):
            quarantined = tuple(LateQuarantineRecord(event, "late_beyond_horizon", now) for event in events)
            return ReplayResult(False, "late_beyond_horizon", (), tuple(sorted({floor_utc(event.event_time, 300) for event in events})), snapshot, quarantined)
        grouped: dict[datetime, list[MetricEvent]] = {}
        for event in events:
            if window_start <= event.event_time < window_end:
                grouped.setdefault(floor_utc(event.event_time, 300), []).append(event)
        rebuilt_list = [self._rebuild_bucket(start, tuple(values)) for start, values in sorted(grouped.items())]
        for metric in payload_metrics:
            if not (window_start <= metric.bucket_start < window_end):
                continue
            payload = json.dumps(metric.to_wire(), sort_keys=True)
            fingerprint = hashlib.sha256(payload.encode()).hexdigest()
            previous = self._fingerprints.get(metric.bucket_start)
            revision = self._revisions.get(metric.bucket_start, 0)
            if previous != fingerprint:
                revision += 1
                self._fingerprints[metric.bucket_start] = fingerprint
                self._revisions[metric.bucket_start] = revision
            rebuilt_list.append(BucketMetric(metric.bucket_start, metric.bucket_end, metric.estimated_people_count, metric.peak_people_count, metric.foot_traffic_count, metric.entry_count, metric.dwell_seconds_sum, metric.completed_dwell_session_count, metric.wifi_observation_count, metric.ble_observation_count, metric.confidence_score, metric.quality_flags, metric.source_detail, metric.threshold_version, metric.metric_version, max(1, revision), metric.generated_at))
        rebuilt = tuple(sorted(rebuilt_list, key=lambda metric: metric.bucket_start))
        return ReplayResult(True, None, rebuilt, tuple(metric.bucket_start for metric in rebuilt), snapshot, ())
