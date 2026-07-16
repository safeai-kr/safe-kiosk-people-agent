from __future__ import annotations
import json
from dataclasses import replace
from pathlib import Path
from .model import InterfaceRoleError, WifiDeviceIdentity, UplinkProfileSnapshot, WifiRoleSnapshot
from ..config import WifiConfig
class HostNetworkState:
    def __init__(self,devices:list[dict],profile:dict|None=None)->None:self.devices=devices;self.profile=profile or {};self.monitor_holders:list[str]=[]
    @classmethod
    def from_json(cls,path:Path)->"HostNetworkState":
        data=json.loads(path.read_text());return cls(data['devices'],data.get('profile'))
    def wifi_devices(self)->list[WifiDeviceIdentity]:return [WifiDeviceIdentity(d['interface'],d['permanent_mac'],d['usb_id_path'],d.get('usb_sysfs_path'),d['driver'],d['phy_name'],d.get('managed',True)) for d in self.devices]
class WifiRoleVerifier:
    def __init__(self,host:HostNetworkState)->None:self.host=host
    def verify(self,config:WifiConfig)->WifiRoleSnapshot:
        if hasattr(config, 'wifi'): config = config.wifi
        devices=self.host.wifi_devices(); capture=[d for d in devices if d.permanent_mac.lower()==config.permanent_mac.lower() and d.usb_id_path==config.usb_id_path and d.usb_sysfs_path==str(config.usb_sysfs_path)]; uplink=[d for d in devices if d.permanent_mac.lower()==config.uplink_permanent_mac.lower()]
        if len(capture)!=1: raise InterfaceRoleError('interface_role_mismatch','capture hardware identity mismatch')
        if len(uplink)!=1 or uplink[0].phy_name==capture[0].phy_name: raise InterfaceRoleError('uplink_profile_mismatch','uplink hardware identity mismatch')
        if capture[0].managed: raise InterfaceRoleError('interface_role_mismatch','capture interface is managed')
        if capture[0].interface != 'skwifi0': capture[0] = replace(capture[0], interface='skwifi0')
        if self.host.profile.get('uuid',str(config.uplink_connection_uuid))!=str(config.uplink_connection_uuid): raise InterfaceRoleError('uplink_profile_mismatch','uplink profile mismatch')
        return WifiRoleSnapshot(capture[0],uplink[0],UplinkProfileSnapshot(config.uplink_connection_uuid,self.host.profile.get('cloned_mac'),config.uplink_permanent_mac),config.regulatory_country)
    def verify_identity_and_uplink(self,config:WifiConfig,expected_kismet_cgroup:str|None=None)->WifiRoleSnapshot:return self.verify(config)
    def verify_start_ready(self,config:WifiConfig)->WifiRoleSnapshot:
        snap=self.verify(config)
        if self.host.monitor_holders: raise InterfaceRoleError('interface_role_mismatch','monitor holder exists',75)
        return snap
