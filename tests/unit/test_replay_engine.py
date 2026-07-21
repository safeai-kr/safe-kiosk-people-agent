from datetime import datetime, timedelta, timezone
from decimal import Decimal

from safe_kiosk_people_agent.domain import BucketMetric, ConfigSnapshot, ScheduledAction, StateSnapshot
from safe_kiosk_people_agent.metrics.replay import ReplayEngine


def metric(start: datetime, count: int) -> BucketMetric:
    return BucketMetric(start, start + timedelta(seconds=300), count, count, 0, 0, Decimal(0), Decimal(0), 1, 0, Decimal("1"), (), {}, "threshold-v1", "metric-v1", 1, start)


def test_same_payload_keeps_revision_and_changed_payload_increments() -> None:
    start = datetime.now(timezone.utc).replace(microsecond=0)
    snapshot = StateSnapshot(start, start, {}, "{}", 1)
    config = ConfigSnapshot(1, "threshold-v1", "digest", start, "{}")
    engine = ReplayEngine()
    action = ScheduledAction("event", start, None, 1, metric(start, 1))
    first = engine.rebuild([action], start - timedelta(seconds=1), start + timedelta(seconds=300), snapshot, {1: config})
    second = engine.rebuild([action], start - timedelta(seconds=1), start + timedelta(seconds=300), snapshot, {1: config})
    changed = engine.rebuild([ScheduledAction("event", start, None, 1, metric(start, 2))], start - timedelta(seconds=1), start + timedelta(seconds=300), snapshot, {1: config})
    assert first.rebuilt_buckets[0].revision == second.rebuilt_buckets[0].revision
    assert changed.rebuilt_buckets[0].revision == first.rebuilt_buckets[0].revision + 1
