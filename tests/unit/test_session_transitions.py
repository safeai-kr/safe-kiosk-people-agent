from datetime import datetime, timedelta, timezone
from decimal import Decimal

from safe_kiosk_people_agent.domain import ClassificationLabel, SessionPolicy, Source
from safe_kiosk_people_agent.metrics.sessions import SessionEngine


def at(seconds: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)


def engine() -> SessionEngine:
    return SessionEngine(SessionPolicy(600, 60, 21600))


def test_outside_then_inside_counts_foot_and_entry_once() -> None:
    service = engine()
    service.apply_observation(Source.WIFI, "token", at(0), ClassificationLabel.OUTSIDE)
    transition = service.apply_observation(Source.WIFI, "token", at(20), ClassificationLabel.INSIDE)
    assert (transition.outcomes[0].foot_traffic_count, transition.outcomes[0].entry_count) == (1, 1)


def test_first_seen_inside_has_no_foot_or_entry() -> None:
    service = engine()
    transition = service.apply_observation(Source.WIFI, "token", at(0), ClassificationLabel.INSIDE)
    assert transition.outcomes == ()
    closed = service.close_timeouts(at(601))[0]
    assert closed.foot_traffic_count == 0
    assert closed.unconfirmed_entry_count == 1


def test_dwell_is_inclusive_at_minimum() -> None:
    service = engine()
    service.apply_observation(Source.BLE, "token", at(0), ClassificationLabel.OUTSIDE)
    service.apply_observation(Source.BLE, "token", at(1), ClassificationLabel.INSIDE)
    service.apply_observation(Source.BLE, "token", at(61), ClassificationLabel.INSIDE)
    outcome = service.close_timeouts(at(661))[0]
    assert outcome.dwell_seconds_sum == Decimal("60")
