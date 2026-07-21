from datetime import datetime
from typing import Literal
from .rate_limit import RecoveryRateLimiter
from .record import RecoveryResult
from .wifi import WifiRecovery
from .bluetooth import BluetoothRecovery

class RecoveryCoordinator:
    def __init__(self, limiter: RecoveryRateLimiter | None = None, wifi: WifiRecovery | None = None, bluetooth: BluetoothRecovery | None = None): self.limiter = limiter or RecoveryRateLimiter(); self.wifi = wifi or WifiRecovery(); self.bluetooth = bluetooth or BluetoothRecovery()
    def recover(self, scope: Literal["wifi", "ble"], now: datetime, *, boot_id: str = "unknown") -> RecoveryResult:
        decision = self.limiter.decide(scope=scope, boot_id=boot_id, now=now, now_boottime_ns=0)
        if not decision.allowed: return RecoveryResult("unavailable", decision.reason, 75)
        identity: dict[str, object] = {"holders": [], "uplink_identifiers": []}
        result = self.wifi.recover(identity, now) if scope == "wifi" else self.bluetooth.recover({"holders": [], "adapter": "hci1"}, now)
        self.limiter.record_attempt(scope=scope, action_id=f"{scope}-{now.timestamp()}", outcome="succeeded" if result.exit_status == 0 else "failed", boot_id=boot_id, occurred_at=now, occurred_boottime_ns=0)
        return result
