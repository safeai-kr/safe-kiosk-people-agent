from __future__ import annotations
from datetime import timedelta
from ..domain import EventPartition,ScheduledAction
class WatermarkCoordinator:
    def partition_events(self,events,processed_through):return EventPartition(tuple(e for e in events if e.event_time>=processed_through),tuple(e for e in events if e.event_time<processed_through))
    def is_late(self,event,processed_through,horizon_seconds=86400):return event.event_time<processed_through-timedelta(seconds=horizon_seconds)
    def closeable_through(self,now,watermarks):return now-timedelta(seconds=30)
    def next_actions(self,events,health_events,tick_after,tick_through):return tuple(ScheduledAction('event',e.event_time,e.source,e.spool_sequence,e) for e in events)
