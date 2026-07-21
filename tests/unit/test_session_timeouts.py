from datetime import datetime, timedelta, timezone

from safe_kiosk_people_agent.domain import ClassificationLabel, SessionPolicy, Source
from safe_kiosk_people_agent.metrics.sessions import SessionEngine


def test_outside_only_counts_foot_at_timeout() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service = SessionEngine(SessionPolicy(600, 60, 21600))
    service.apply_observation(Source.BLE, "token", start, ClassificationLabel.OUTSIDE)
    [outcome] = service.close_timeouts(start + timedelta(seconds=600))
    assert (outcome.foot_traffic_count, outcome.entry_count, outcome.timeout_closed_count) == (1, 0, 1)


def test_source_interrupt_closes_without_traffic() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service = SessionEngine(SessionPolicy(600, 60, 21600))
    service.apply_observation(Source.WIFI, "token", start, ClassificationLabel.OUTSIDE)
    [outcome] = service.interrupt_source(Source.WIFI, start + timedelta(seconds=10))
    assert outcome.foot_traffic_count == 0
    assert outcome.interrupted_session_count == 1
    assert outcome.quality_flags == ("source_outage_interrupted",)
