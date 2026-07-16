from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from threading import Event
from typing import Iterable
from ..domain import NewObservationSummary, ProtocolThresholds, Source
from ..clock import floor_utc
@dataclass(frozen=True)
class MetricBucket:
    bucket_start:datetime; estimated_people_count:int; peak_people_count:int; observation_count:int; sources:tuple[Source,...]
class MetricsWorker:
    """Deterministic in-process reducer; upload is deliberately handled by Task 12."""
    def __init__(self, thresholds:dict[Source,ProtocolThresholds]): self.thresholds=thresholds
    def reduce(self,summaries:Iterable[NewObservationSummary])->tuple[MetricBucket,...]:
        groups:dict[datetime,list[NewObservationSummary]]={}
        for summary in summaries: groups.setdefault(floor_utc(summary.window_start,300),[]).append(summary)
        result=[]
        for start, values in sorted(groups.items()):
            inside={ (v.source,v.device_token) for v in values if v.median_rssi_dbm >= self.thresholds[v.source].inside_rssi_dbm }
            result.append(MetricBucket(start,len(inside),len(inside),len(values),tuple(sorted({v.source for v in values},key=lambda x:x.value))))
        return tuple(result)
    def run(self,stop:Event,supplier,*,max_cycles:int|None=None)->tuple[MetricBucket,...]:
        all_values=[]; cycles=0
        while not stop.is_set() and (max_cycles is None or cycles<max_cycles):
            all_values.extend(supplier()); cycles+=1
        return self.reduce(all_values)
