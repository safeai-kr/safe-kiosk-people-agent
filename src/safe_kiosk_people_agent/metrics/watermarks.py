from __future__ import annotations
from datetime import timedelta
from datetime import datetime
from ..domain import EventPartition, HealthEvent, MetricEvent, ScheduledAction


class WatermarkCoordinator:
    def partition_events(self, events, processed_through):
        return EventPartition(tuple(e for e in events if e.event_time >= processed_through), tuple(e for e in events if e.event_time < processed_through))

    def is_late(self, event, processed_through, horizon_seconds=86400):
        return event.event_time < processed_through - timedelta(seconds=horizon_seconds)

    def closeable_through(self, now: datetime, watermarks):
        return now - timedelta(seconds=30)

    def next_actions(self, events: tuple[MetricEvent, ...], health_events: tuple[HealthEvent, ...], tick_after: datetime, tick_through: datetime) -> tuple[ScheduledAction, ...]:
        actions = [ScheduledAction("event", event.event_time, event.source, event.spool_sequence, event) for event in events]
        actions.extend(ScheduledAction("health", event.observed_at, event.source, 0, event) for event in health_events)
        cursor = tick_after
        while cursor <= tick_through:
            actions.append(ScheduledAction("tick", cursor, None, 0, None))
            cursor += timedelta(seconds=10)
        return tuple(sorted(actions, key=lambda action: (action.at, action.kind, action.source.value if action.source else "", action.spool_sequence)))
