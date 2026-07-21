from datetime import datetime, timedelta, timezone

from safe_kiosk_people_agent.recovery.rate_limit import RecoveryRateLimiter


def test_three_failures_then_cooldown_and_hourly_limit() -> None:
    limiter = RecoveryRateLimiter()
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for index in range(3):
        limiter.record_failure(scope="wifi", unit="wifi", service_result="failed", boot_id="boot", occurred_at=start + timedelta(seconds=index), occurred_boottime_ns=0)
    assert limiter.decide(scope="wifi", boot_id="boot", now=start + timedelta(seconds=61), now_boottime_ns=0).allowed
