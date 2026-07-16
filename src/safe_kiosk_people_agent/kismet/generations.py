from __future__ import annotations
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from ..domain import KismetGeneration
class KismetGenerationManager:
    def __init__(self): self.current=None
    def start(self,generation_id:str,path:Path,boot_id:str,created_at:datetime)->KismetGeneration:
        self.current=KismetGeneration(generation_id,path,'active',boot_id,None,None,None,created_at,None,None);return self.current
    def close(self,closed_at:datetime)->KismetGeneration:
        if self.current is None: raise RuntimeError('no active generation')
        self.current=replace(self.current,state='closed',closed_at=closed_at);return self.current
