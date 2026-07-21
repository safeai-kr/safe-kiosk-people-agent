from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Event
from typing import Callable, Iterable
from ..collectors.summary import TenSecondSummarizer
from ..domain import Source, SourceHealth, NewObservationSummary, SourceWatermark
from ..storage.spool import BleSpool
from .collector import BleAdvertisement, BleObservationCollector

@dataclass(frozen=True)
class BleWorkerResult:
    summaries:tuple[NewObservationSummary,...]
    cycles:int
    health:SourceHealth

class BleCollectorWorker:
    def __init__(self, collector:BleObservationCollector, advertisements:Callable[[],Iterable[BleAdvertisement]], *, clock:Callable[[],datetime]=lambda: datetime.now(timezone.utc), spool:BleSpool|None=None, boot_id:str="unknown"):
        self.collector=collector; self.advertisements=advertisements; self.clock=clock; self.spool=spool; self.boot_id=boot_id
    def run(self, stop:Event, *, max_cycles:int|None=None)->BleWorkerResult:
        summarizer=TenSecondSummarizer(source=Source.BLE,collector_run_id=self.collector.collector_run_id)
        summaries:list[NewObservationSummary]=[]; cycles=0
        try:
            while not stop.is_set() and (max_cycles is None or cycles<max_cycles):
                for value in self.collector.normalize(self.advertisements()): summarizer.add(value)
                cycles+=1
                now = self.clock().astimezone(timezone.utc)
                flushed = summarizer.flush_through(now)
                summaries.extend(flushed)
                if self.spool is not None:
                    progress = cycles
                    sequence = self.spool.current_sequence() + len(flushed)
                    watermark = SourceWatermark(Source.BLE, self.collector.collector_run_id, self.boot_id, now, now, sequence, SourceHealth.HEALTHY, now, 0, progress)
                    self.spool.append_window(flushed, watermark)
            return BleWorkerResult(tuple(summaries),cycles,SourceHealth.HEALTHY)
        except Exception:
            return BleWorkerResult(tuple(summaries),cycles,SourceHealth.DEGRADED)
