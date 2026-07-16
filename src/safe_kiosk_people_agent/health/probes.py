from __future__ import annotations
from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol
from .systemd import SystemdNotifier

class ProbeFailed(RuntimeError): pass
class BootClock(Protocol):
    def boottime_ns(self) -> int: ...
@dataclass(frozen=True)
class ProbeResult: ok:bool; progress_sequence:int; checked_boottime_ns:int; detail:str
class WatchdogLoop:
    def __init__(self,notifier:SystemdNotifier,clock:BootClock)->None:self.notifier=notifier;self.clock=clock;self.last_progress_sequence=-1;self.ready=False
    async def run_once(self,probe:Callable[[],Awaitable[ProbeResult]])->ProbeResult:
        result=await probe()
        if not result.ok: raise ProbeFailed(result.detail)
        now=self.clock.boottime_ns()
        if result.progress_sequence<=self.last_progress_sequence: raise ProbeFailed("probe progress did not advance")
        if now-result.checked_boottime_ns>40_000_000_000: raise ProbeFailed("probe progress is stale")
        if result.checked_boottime_ns>now+5_000_000_000: raise ProbeFailed("probe progress is in the future")
        self.last_progress_sequence=result.progress_sequence
        if not self.ready:self.notifier.ready(result.detail);self.ready=True
        self.notifier.watchdog(result.detail);return result
