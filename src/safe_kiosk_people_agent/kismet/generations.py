from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timedelta
from uuid import uuid4
from pathlib import Path
from ..domain import KismetGeneration
class KismetGenerationManager:
    def __init__(self,root:Path|None=None,max_age_seconds:int=43200): self.current:KismetGeneration|None=None; self.root=root; self.max_age=timedelta(seconds=max_age_seconds); self.generations:dict[str,KismetGeneration]={}
    def create(self,now:datetime)->KismetGeneration:
        gid=uuid4().hex; path=(self.root or Path('.'))/'generations'/f'{gid}.kismet'; path.parent.mkdir(parents=True,exist_ok=True)
        return self.start(gid,path,'unknown',now)
    def start(self,generation_id:str,path:Path,boot_id:str,created_at:datetime)->KismetGeneration:
        self.current=KismetGeneration(generation_id,path,'active',boot_id,None,None,None,created_at,None,None); self.generations[generation_id]=self.current; return self.current
    def mark_closed(self,generation_id:str,at:datetime)->None:
        g=self.generations[generation_id]; self.generations[generation_id]=replace(g,state='closed',closed_at=at)
    def mark_consumed(self,generation_id:str,cursor:object,at:datetime)->None:
        g=self.generations[generation_id]; self.generations[generation_id]=replace(g,state='consumed',closed_at=g.closed_at or at)
    def should_rotate(self,generation:KismetGeneration,now:datetime)->bool: return now-generation.created_at >= self.max_age
    def delete_consumed(self,generation_ids:list[str])->None:
        for gid in generation_ids:
            g=self.generations.get(gid)
            if g and g.state=='consumed':
                for p in (g.path,Path(str(g.path)+'-wal'),Path(str(g.path)+'-shm')):
                    if p.exists(): p.unlink()
                del self.generations[gid]
    def close(self,closed_at:datetime)->KismetGeneration:
        if self.current is None: raise RuntimeError('no active generation')
        self.mark_closed(self.current.generation_id,closed_at); self.current=self.generations[self.current.generation_id]; return self.current
