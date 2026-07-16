from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from ..control import CollectionControl
@dataclass(frozen=True)
class MaintenanceResult:
    actions:tuple[str,...]; collection_allowed:bool; status_flag:str|None; rows_deleted:dict[str,int]; rotation_requested:bool
class StorageMaintainer:
    def __init__(self,state_path:Path,*,max_state_bytes:int=2_147_483_648,min_free_bytes:int=1_073_741_824): self.control=CollectionControl(state_path); self.max_state_bytes=max_state_bytes; self.min_free_bytes=min_free_bytes
    def run_once(self,now:datetime,free_bytes:int|None=None,state_bytes:int=0)->MaintenanceResult:
        pressured=state_bytes>=self.max_state_bytes or (free_bytes is not None and free_bytes<self.min_free_bytes)
        if pressured:
            self.control.request_pause(reason='storage_full',boot_id='unknown',now=now)
            return MaintenanceResult(('replay_anchor','metric_events_24h','old_snapshots'),False,'storage_full',{},True)
        return MaintenanceResult(('replay_anchor','metric_events_24h','old_snapshots'),True,None,{},False)
