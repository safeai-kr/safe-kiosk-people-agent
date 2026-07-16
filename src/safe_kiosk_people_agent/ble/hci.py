from __future__ import annotations
from dataclasses import dataclass
import subprocess
from pathlib import Path
from typing import Callable, Sequence

class BleHciError(RuntimeError): pass
@dataclass(frozen=True)
class BleHciStatus:
    adapter:str; permanent_address:str|None; powered:bool; discovering:bool

class BleHciController:
    """Resolves an HCI adapter by USB identity and clears stale ownership before use."""
    def __init__(self, adapter:str, usb_sysfs_path:Path, run:Callable[...,subprocess.CompletedProcess[str]]|None=None):
        self.adapter=adapter; self.usb_sysfs_path=usb_sysfs_path; self._run=run or subprocess.run
    def _command(self,args:Sequence[str],check:bool=True)->str:
        result=self._run(tuple(args),capture_output=True,text=True,check=False)
        if check and result.returncode: raise BleHciError(f"{' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout
    def verify_identity(self)->None:
        if not self.adapter.startswith('hci') or not self.usb_sysfs_path.is_absolute(): raise BleHciError('unsafe HCI identity')
        if not self.usb_sysfs_path.exists(): raise BleHciError('configured HCI USB path is absent')
    def release_stale_owner(self)->None:
        self._command(('sudo','hciconfig',self.adapter,'down'),check=False)
        self._command(('sudo','pkill','-TERM','-f',f'bluetooth.*{self.adapter}'),check=False)
        self._command(('sudo','hciconfig',self.adapter,'reset'),check=False)
    def prepare(self)->BleHciStatus:
        self.verify_identity(); self.release_stale_owner()
        self._command(('sudo','hciconfig',self.adapter,'up'))
        self._command(('sudo','hciconfig',self.adapter,'piscan'),check=False)
        info=self._command(('hciconfig',self.adapter),check=False)
        return BleHciStatus(self.adapter,None,'UP RUNNING' in info,'PSCAN' in info or 'ISCAN' in info)
