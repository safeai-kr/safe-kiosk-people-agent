from datetime import datetime
from typing import Literal
from .rate_limit import RecoveryRateLimiter
from .record import RecoveryResult

class RecoveryCoordinator:
    def __init__(self, limiter: RecoveryRateLimiter | None = None): self.limiter = limiter or RecoveryRateLimiter()
    def recover(self, scope: Literal["wifi", "ble"], now: datetime, *, boot_id: str = "unknown") -> RecoveryResult:
        decision = self.limiter.decide(scope=scope, boot_id=boot_id, now=now, now_boottime_ns=0)
        if not decision.allowed: return RecoveryResult("unavailable", decision.reason, 75)
        self.limiter.record_attempt(scope=scope, action_id=f"{scope}-{now.timestamp()}", outcome="failed", boot_id=boot_id, occurred_at=now, occurred_boottime_ns=0)
        return RecoveryResult("recovering", "recovery_dispatch_pending", 75)
