from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc
BUCKET_SECONDS = 300


def floor_utc(value: datetime, seconds: int) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    value = value.astimezone(UTC)
    epoch = int(value.timestamp())
    return datetime.fromtimestamp(epoch - epoch % seconds, UTC)


def bucket_bounds(value: datetime) -> tuple[datetime, datetime]:
    start = floor_utc(value, BUCKET_SECONDS)
    return start, start + timedelta(seconds=BUCKET_SECONDS)
