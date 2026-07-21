from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class Tick:
    at: datetime
    index: int


class TickBuilder:
    tick_seconds = 10

    def build(self, bucket_start: datetime, bucket_end: datetime) -> tuple[Tick, ...]:
        if bucket_start.tzinfo is None or bucket_end.tzinfo is None:
            raise ValueError("tick boundaries must be timezone-aware")
        start = bucket_start.astimezone(timezone.utc)
        end = bucket_end.astimezone(timezone.utc)
        if end <= start or (end - start).total_seconds() % self.tick_seconds:
            raise ValueError("bucket must contain complete 10-second ticks")
        count = int((end - start).total_seconds() // self.tick_seconds)
        return tuple(Tick(start + timedelta(seconds=i * self.tick_seconds), i) for i in range(count))
