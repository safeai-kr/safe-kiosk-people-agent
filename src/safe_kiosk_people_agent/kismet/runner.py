from __future__ import annotations
from subprocess import Popen
from threading import Event
from typing import Callable, Sequence
from ..interfaces.discovery import WifiRoleSnapshot
from ..health.systemd import SystemdNotifier
from ..health.watchdog import WatchdogLoop  # type: ignore[import-untyped]
class KismetRunner:
    def __init__(self,before_spawn:Callable[[],WifiRoleSnapshot],notifier:SystemdNotifier,watchdog:WatchdogLoop,command:Sequence[str]=( 'true',)):
        self.before_spawn=before_spawn; self.notifier=notifier; self.watchdog=watchdog; self.command=tuple(command)
    def run(self,stop:Event)->int:
        try: self.before_spawn()
        except Exception: return 78
        if stop.is_set(): return 0
        self.notifier.status('kismet starting')
        proc=Popen(self.command, start_new_session=True)
        return proc.wait()
