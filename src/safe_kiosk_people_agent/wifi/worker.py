from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol

from ..collectors.summary import TenSecondSummarizer
from ..domain import KismetCursor, KismetGeneration, Source, SourceHealth, SourceWatermark
from ..kismet.reader import KismetReader
from ..wifi.collector import WifiObservationCollector
from ..storage.spool import WifiSpool


@dataclass(frozen=True)
class WifiWorkerResult:
    summaries_written: int
    progress_sequence: int
    health: SourceHealth


class GenerationSource(Protocol):
    current: KismetGeneration | None


class WifiCollectorWorker:
    def __init__(
        self,
        collector: WifiObservationCollector,
        reader: KismetReader,
        generations: GenerationSource,
        spool: WifiSpool,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        boot_id: str = "unknown",
        batch_size: int = 1000,
    ) -> None:
        self.collector = collector
        self.reader = reader
        self.generations = generations
        self.spool = spool
        self.clock = clock
        self.boot_id = boot_id
        self.batch_size = batch_size
        self.summarizer = TenSecondSummarizer(source=Source.WIFI, collector_run_id=collector.collector_run_id)
        existing = spool.read_watermark()
        self.progress_sequence = existing.progress_sequence if existing is not None else 0

    async def run_once(self) -> WifiWorkerResult:
        current = self.generations.current
        if current is None:
            raise RuntimeError("no active Kismet generation")
        generation: KismetGeneration = current
        cursor = self.spool.read_cursor(generation.generation_id) or KismetCursor(generation.generation_id, 0, 0, 0)
        packets = self.reader.read_probe_requests(generation, cursor, self.batch_size)
        for observation in self.collector.normalize(packets):
            self.summarizer.add(observation)
        now = self.clock().astimezone(timezone.utc)
        summaries = self.summarizer.flush_through(now)
        self.progress_sequence += 1
        next_cursor = cursor
        if packets:
            packet = packets[-1]
            next_cursor = KismetCursor(generation.generation_id, packet.ts_sec, packet.ts_usec, packet.rowid)
        caught_up = max((p.observed_at for p in packets), default=now)
        next_sequence = self.spool.current_sequence() + len(summaries)
        source_watermark = SourceWatermark(Source.WIFI, self.collector.collector_run_id, self.boot_id, now, caught_up, next_sequence, SourceHealth.HEALTHY, now, 0, self.progress_sequence)
        self.spool.append_poll(generation.generation_id, next_cursor, summaries, source_watermark)
        return WifiWorkerResult(len(summaries), self.progress_sequence, SourceHealth.HEALTHY)

    async def run(self, stop: asyncio.Event, *, max_cycles: int | None = None) -> WifiWorkerResult:
        cycles = 0
        last = WifiWorkerResult(0, self.progress_sequence, SourceHealth.HEALTHY)
        try:
            while not stop.is_set() and (max_cycles is None or cycles < max_cycles):
                last = await self.run_once()
                cycles += 1
            return last
        except Exception:
            return WifiWorkerResult(0, self.progress_sequence, SourceHealth.DEGRADED)
