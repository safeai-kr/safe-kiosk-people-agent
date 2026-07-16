from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Callable, Iterable
from ..domain import Source, SourceHealth, NewObservationSummary
from .worker import MetricsWorker

class MetricsService:
    """Small deterministic scheduler boundary; transport runs in a separate task."""
    def __init__(self, worker:MetricsWorker, supplier:Callable[[],Iterable[NewObservationSummary]]=lambda: (), *, uploader=None, clock:Callable[[],datetime]=lambda: datetime.now(timezone.utc)):
        self.worker=worker; self.supplier=supplier; self.uploader=uploader; self.clock=clock
        self.health={Source.WIFI:SourceHealth.HEALTHY,Source.BLE:SourceHealth.HEALTHY}; self._pending:list[NewObservationSummary]=[]
    def record_health(self,source:Source,health:SourceHealth,at:datetime)->None: self.health[source]=health
    async def run_once(self,now:datetime|None=None):
        _ = now or self.clock(); values=list(self.supplier()); self._pending.extend(values)
        buckets=self.worker.reduce(self._pending); self._pending.clear()
        quality=tuple(f'{source.value}_unavailable' for source,state in self.health.items() if state==SourceHealth.UNAVAILABLE)
        return buckets, quality
    async def run(self,stop:asyncio.Event)->None:
        while not stop.is_set():
            await self.run_once(self.clock())
            try: await asyncio.wait_for(stop.wait(),10)
            except asyncio.TimeoutError: pass

async def run_metrics_service(service:MetricsService,stop:asyncio.Event)->None:
    tasks=[asyncio.create_task(service.run(stop))]
    if service.uploader is not None: tasks.append(asyncio.create_task(service.uploader.run_resilient(stop)))
    await asyncio.gather(*tasks)
