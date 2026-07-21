from datetime import datetime, timezone

from safe_kiosk_people_agent.domain import ClassificationLabel, SessionPolicy, Source
from safe_kiosk_people_agent.metrics.sessions import SessionEngine


def test_expired_fixed_mark_can_be_removed() -> None:
    service = SessionEngine(SessionPolicy(600, 60, 21600, fixed_mark_seconds=10))
    at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.apply_observation(Source.WIFI, "token", at, ClassificationLabel.INSIDE)
    service.apply_observation(Source.WIFI, "token", at.replace(day=2), ClassificationLabel.INSIDE)
    assert service.expire_fixed_marks(at.replace(day=3))
