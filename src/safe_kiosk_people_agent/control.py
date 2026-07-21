from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import time
from pathlib import Path
from typing import Literal
@dataclass(frozen=True)
class CollectionState:
    generation:int; state:Literal['running','pause_requested','paused','resume_requested']; reason:str; boot_id:str; requested_at:datetime; observed_at:datetime
class CollectionControl:
    def __init__(self,path:Path): self.path=path
    def read(self)->CollectionState:
        if not self.path.exists():
            now=datetime.now(timezone.utc); return CollectionState(0,'running','startup','unknown',now,now)
        value=json.loads(self.path.read_text()); return CollectionState(value['generation'],value['state'],value['reason'],value['boot_id'],datetime.fromisoformat(value['requested_at']),datetime.fromisoformat(value['observed_at']))
    def _write(self,state:CollectionState)->CollectionState:
        self.path.parent.mkdir(parents=True,exist_ok=True); tmp=self.path.with_suffix('.tmp')
        payload=json.dumps({**asdict(state),'requested_at':state.requested_at.isoformat(),'observed_at':state.observed_at.isoformat()},sort_keys=True)
        with tmp.open('w') as stream:
            stream.write(payload); stream.flush(); __import__('os').fsync(stream.fileno())
        tmp.replace(self.path)
        try:
            fd = __import__('os').open(self.path.parent, __import__('os').O_RDONLY)
            try: __import__('os').fsync(fd)
            finally: __import__('os').close(fd)
        except OSError:
            pass
        return state
    def request_pause(self,*,reason:str,boot_id:str,now:datetime)->CollectionState:
        old=self.read(); return self._write(CollectionState(old.generation+1,'pause_requested',reason,boot_id,now,now))
    def request_resume(self,*,reason:str,boot_id:str,now:datetime,paused_generation:int|None=None)->CollectionState:
        old=self.read(); return self._write(CollectionState(old.generation+1,'resume_requested',reason,boot_id,now,now))

    def acknowledge(self, component: str, generation: int, *, state: str = "paused") -> None:
        path = self.path.parent / "acks" / f"{component}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"component": component, "generation": generation, "state": state}, sort_keys=True))

    def wait_for_ack(self, *, generation: int, required: set[str], timeout_seconds: int) -> bool:
        deadline = time.monotonic() + timeout_seconds
        ack_dir = self.path.parent / "acks"
        if not ack_dir.exists():
            return False
        while time.monotonic() < deadline:
            acknowledged = set()
            for component in required:
                path = self.path.parent / "acks" / f"{component}.json"
                if not path.exists():
                    continue
                try:
                    value = json.loads(path.read_text())
                except json.JSONDecodeError:
                    continue
                if value.get("generation") == generation and value.get("state") == "paused":
                    acknowledged.add(component)
            if acknowledged == required:
                return True
            time.sleep(0.01)
        return False
