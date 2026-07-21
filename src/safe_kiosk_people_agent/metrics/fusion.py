from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Mapping

from ..domain import BucketMetric, ProtocolSourceDetail, Source


def weighted_inside_count(values: Mapping[Source, int | None], weights: Mapping[Source, Decimal]) -> int:
    available = [(source, count) for source, count in values.items() if count is not None]
    if not available:
        return 0
    total_weight = sum((weights.get(source, Decimal(0)) for source, _ in available), Decimal(0))
    if total_weight <= 0:
        return 0
    return int(round(sum((Decimal(count) * weights.get(source, Decimal(0)) for source, count in available), Decimal(0)) / total_weight))


def build_bucket_metric(
    bucket_start: datetime,
    inside_ticks: Mapping[Source, int | None],
    source_detail: Mapping[Source, ProtocolSourceDetail],
    weights: Mapping[Source, Decimal],
    *,
    threshold_version: str = "manual",
    metric_version: str = "metric-v1",
    revision: int = 1,
    generated_at: datetime | None = None,
    observation_counts: Mapping[Source, int] | None = None,
) -> BucketMetric | None:
    if bucket_start.tzinfo is None:
        raise ValueError("bucket_start must be timezone-aware")
    healthy = [source for source, value in inside_ticks.items() if value is not None]
    if not healthy:
        return None
    generated = (generated_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    estimated = weighted_inside_count(inside_ticks, weights)
    peak = max((value or 0 for value in inside_ticks.values()), default=0)
    quality: list[str] = []
    for source in Source:
        if inside_ticks.get(source) is None:
            quality.append(f"{source.value}_unavailable")
    confidence = Decimal("1.0") if len(healthy) == 2 else Decimal("0.5")
    return BucketMetric(
        bucket_start.astimezone(timezone.utc), bucket_start.astimezone(timezone.utc) + timedelta(seconds=300),
        estimated, peak,
        sum(detail.foot_traffic_count for detail in source_detail.values()),
        sum(detail.entry_count for detail in source_detail.values()),
        sum((detail.dwell_seconds_sum for detail in source_detail.values()), Decimal(0)),
        sum((detail.completed_dwell_session_count for detail in source_detail.values()), Decimal(0)),
        (observation_counts or {}).get(Source.WIFI, 0),
        (observation_counts or {}).get(Source.BLE, 0),
        confidence, tuple(quality), source_detail, threshold_version, metric_version, revision, generated,
    )
