from __future__ import annotations
import json
from pathlib import Path
from ..domain import ComponentStatus, SensorError, SourceHealth
class ComponentStatusStore:
    def __init__(self,root:Path):self.root=root
    def publish(self,component:str,health:SourceHealth,error:SensorError|None,*,latched:bool)->None:
        self.root.mkdir(parents=True,exist_ok=True); path=self.root/(component+'.json'); tmp=path.with_suffix('.tmp')
        data={'component':component,'health':health.value,'error':None if error is None else {'component':error.component,'code':error.code,'message':error.message[:512],'occurred_at':error.occurred_at.isoformat()},'latched':latched}
        tmp.write_text(json.dumps(data,sort_keys=True));tmp.replace(path)
    def read(self,component:str)->ComponentStatus|None:
        path=self.root/(component+'.json')
        if not path.exists(): return None
        data=json.loads(path.read_text()); return ComponentStatus(data['component'],SourceHealth(data['health']),None,data['latched'],'',0,__import__('datetime').datetime.now().astimezone(),0)
