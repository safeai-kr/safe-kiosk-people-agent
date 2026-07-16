from datetime import datetime, timezone
from safe_kiosk_people_agent.clock import bucket_bounds

def test_bucket_bounds_are_utc_half_open() -> None:
    start, end = bucket_bounds(datetime(2026, 7, 14, 12, 7, 29, tzinfo=timezone.utc))
    assert start == datetime(2026, 7, 14, 12, 5, tzinfo=timezone.utc)
    assert end == datetime(2026, 7, 14, 12, 10, tzinfo=timezone.utc)
