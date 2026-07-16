from __future__ import annotations
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import median_low
from typing import Sequence
from ..clock import floor_utc
from ..domain import NewObservationSummary, Source

@dataclass(frozen=True)
class TokenizedObservation:
    origin_id: str; source: Source; device_token: str; observed_at: datetime; rssi_dbm: int; frequency_mhz: float|None; tx_power_dbm: int|None

def make_summary_id(source: Source, device_token: str, window_start: datetime, origin_ids: Sequence[str]) -> str:
    canonical = "\n".join((source.value, device_token, window_start.isoformat(), *sorted(origin_ids)))
    return hashlib.sha256(canonical.encode()).hexdigest()

class TenSecondSummarizer:
    def __init__(self, *, source: Source, collector_run_id: str) -> None:
        if not collector_run_id.strip(): raise ValueError("collector_run_id is required")
        self.source, self.collector_run_id = source, collector_run_id
        self._observations: list[TokenizedObservation] = []
    def add(self, observation: TokenizedObservation) -> None:
        if observation.source != self.source: raise ValueError("observation source does not match summarizer")
        if observation.observed_at.tzinfo is None: raise ValueError("observation timestamp must be timezone-aware")
        self._observations.append(observation)
    def flush_through(self, through: datetime) -> tuple[NewObservationSummary, ...]:
        if through.tzinfo is None: raise ValueError("through timestamp must be timezone-aware")
        through = through.astimezone(timezone.utc)
        complete = [o for o in self._observations if floor_utc(o.observed_at, 10) + timedelta(seconds=10) <= through]
        self._observations = [o for o in self._observations if o not in complete]
        groups: dict[tuple[datetime,str], list[TokenizedObservation]] = {}
        for obs in complete: groups.setdefault((floor_utc(obs.observed_at, 10), obs.device_token), []).append(obs)
        result = []
        for (start, token), values in sorted(groups.items()):
            rssis = [v.rssi_dbm for v in values]
            origins = [v.origin_id for v in values]
            result.append(NewObservationSummary(make_summary_id(self.source, token, start, origins), self.source, self.collector_run_id, token, start, start+timedelta(seconds=10), min(v.observed_at for v in values), max(v.observed_at for v in values), len(values), int(median_low(rssis)), max(rssis), values[-1].frequency_mhz, values[-1].tx_power_dbm))
        return tuple(result)
