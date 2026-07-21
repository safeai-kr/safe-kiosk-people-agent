from datetime import datetime, timedelta, timezone

from safe_kiosk_people_agent.domain import ClassificationLabel, SessionPolicy, Source
from safe_kiosk_people_agent.metrics.sessions import SessionEngine


def test_continuous_inside_over_six_hours_becomes_fixed() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service = SessionEngine(SessionPolicy(600, 60, 21600))
    service.apply_observation(Source.WIFI, "token", start, ClassificationLabel.INSIDE)
    transition = service.apply_observation(Source.WIFI, "token", start + timedelta(seconds=21601), ClassificationLabel.INSIDE)
    assert transition.fixed_mark is not None
    assert transition.outcomes == ()
