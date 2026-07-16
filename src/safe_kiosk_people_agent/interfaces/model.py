from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
class InterfaceRoleError(RuntimeError):
    def __init__(self,code:str,message:str,exit_status:int=78)->None: super().__init__(message);self.code=code;self.exit_status=exit_status
@dataclass(frozen=True)
class WifiDeviceIdentity: interface:str; permanent_mac:str; usb_id_path:str; usb_sysfs_path:str|None; driver:str; phy_name:str; managed:bool
@dataclass(frozen=True)
class UplinkProfileSnapshot: uuid:UUID; cloned_mac_policy:str|None; permanent_mac:str
@dataclass(frozen=True)
class WifiRoleSnapshot: capture:WifiDeviceIdentity; uplink:WifiDeviceIdentity; uplink_profile:UplinkProfileSnapshot; country:str
