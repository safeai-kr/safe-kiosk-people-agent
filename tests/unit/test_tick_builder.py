from datetime import datetime, timedelta, timezone

from safe_kiosk_people_agent.metrics.ticks import TickBuilder


def test_closed_bucket_contains_thirty_ten_second_ticks() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ticks = TickBuilder().build(start, start + timedelta(seconds=300))
    assert len(ticks) == 30
    assert ticks[0].at == start and ticks[-1].at == start + timedelta(seconds=290)
