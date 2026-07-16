from __future__ import annotations
import json
from pathlib import Path
from typing import Mapping
class RecoveryCountStore:
    COUNTERS=("wifi_process_restart","wifi_interface_reset","wifi_usb_rebind","ble_process_restart","ble_hci_reset","ble_usb_rebind")
    def __init__(self,path:Path):self.path=path;self._last={k:0 for k in self.COUNTERS}
    def publish_as_root(self,snapshot:Mapping[str,object])->None:
        self.path.parent.mkdir(parents=True,exist_ok=True);tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(snapshot,sort_keys=True));tmp.replace(self.path)
    def read_lifetime_counts(self)->Mapping[str,int]:
        data=json.loads(self.path.read_text()); values=data['lifetime_counts']
        if set(values)!=set(self.COUNTERS) or any(not isinstance(v,int) or v<self._last[k] for k,v in values.items()): raise ValueError('invalid recovery count snapshot')
        self._last=dict(values);return dict(values)
