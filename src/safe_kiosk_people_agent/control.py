from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
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
        self.path.parent.mkdir(parents=True,exist_ok=True); tmp=self.path.with_suffix('.tmp'); tmp.write_text(json.dumps({**asdict(state),'requested_at':state.requested_at.isoformat(),'observed_at':state.observed_at.isoformat()})); tmp.replace(self.path); return state
    def request_pause(self,*,reason:str,boot_id:str,now:datetime)->CollectionState:
        old=self.read(); return self._write(CollectionState(old.generation+1,'pause_requested',reason,boot_id,now,now))
    def request_resume(self,*,reason:str,boot_id:str,now:datetime)->CollectionState:
        old=self.read(); return self._write(CollectionState(old.generation+1,'resume_requested',reason,boot_id,now,now))
