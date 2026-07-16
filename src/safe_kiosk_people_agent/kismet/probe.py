from __future__ import annotations
from dataclasses import dataclass
from ..domain import KismetProbe, KismetCursor
@dataclass(frozen=True)
class KismetProbeRunner:
    datasource:str='skwifi0'; monitor_vif:str='skwifi0mon'
    def check(self,generation_id:str,sequence:int,boottime_ns:int,cursor:KismetCursor|None=None)->KismetProbe:
        return KismetProbe(generation_id,self.datasource,self.monitor_vif,sequence,boottime_ns,cursor)
