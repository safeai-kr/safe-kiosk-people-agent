from datetime import datetime, timedelta, timezone

from safe_kiosk_people_agent.domain import ConfigSnapshot, StateSnapshot
from safe_kiosk_people_agent.metrics.replay import ReplayEngine


def test_replay_beyond_24_hours_is_quarantined() -> None:
    now = datetime.now(timezone.utc)
    snapshot = StateSnapshot(now, now, {}, "{}", 1)
    config = ConfigSnapshot(1, "threshold-v1", "digest", now, "{}")
    result = ReplayEngine().rebuild([], now - timedelta(hours=25), now, snapshot, {1: config})
    assert not result.applied and result.reason == "late_beyond_horizon"
