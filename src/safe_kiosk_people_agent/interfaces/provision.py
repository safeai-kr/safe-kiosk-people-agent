from dataclasses import dataclass
from ..config import WifiConfig
@dataclass(frozen=True)
class ProvisionPlan: profile_changes:dict[str,str|None]
class WifiRoleProvisioner:
    def prepare(self,config:WifiConfig)->ProvisionPlan:return ProvisionPlan({'connection.interface-name':None,'802-11-wireless.mac-address':config.uplink_permanent_mac})
