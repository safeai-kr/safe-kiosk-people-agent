from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

@dataclass(frozen=True)
class RecoveryDecision:
    allowed: bool
    reason: str
    qualifying_failure_count: int
    hardware_attempt_count: int

class RecoveryRateLimiter:
    def __init__(self, cooldown_seconds: int = 60, max_attempts_per_hour: int = 6):
        self.cooldown = timedelta(seconds=cooldown_seconds); self.max_attempts = max_attempts_per_hour
        self.failures: dict[str, list[datetime]] = {}; self.attempts: dict[str, list[datetime]] = {}; self.boot_id = ""
    def record_failure(self, *, scope: Literal["wifi", "ble"], unit: str, service_result: str, boot_id: str, occurred_at: datetime, occurred_boottime_ns: int) -> None:
        if service_result in {"success", "clean-exit", "exit-code-78"}: return
        self.failures.setdefault(scope, []).append(occurred_at); self.boot_id = boot_id
    def decide(self, *, scope: Literal["wifi", "ble"], boot_id: str, now: datetime, now_boottime_ns: int) -> RecoveryDecision:
        if boot_id != self.boot_id: self.failures[scope] = []; self.attempts[scope] = []; self.boot_id = boot_id
        failures = [t for t in self.failures.get(scope, []) if now - t <= timedelta(minutes=10)]
        attempts = [t for t in self.attempts.get(scope, []) if now - t <= timedelta(hours=1)]
        if len(attempts) >= self.max_attempts: return RecoveryDecision(False, "hourly_limit", len(failures), len(attempts))
        if attempts and now - attempts[-1] < self.cooldown: return RecoveryDecision(False, "cooldown", len(failures), len(attempts))
        if len(failures) < 3: return RecoveryDecision(False, "failure_threshold_not_met", len(failures), len(attempts))
        return RecoveryDecision(True, "eligible", len(failures), len(attempts))
    def record_attempt(self, *, scope: Literal["wifi", "ble"], action_id: str, outcome: Literal["succeeded", "failed"], boot_id: str, occurred_at: datetime, occurred_boottime_ns: int) -> None:
        self.attempts.setdefault(scope, []).append(occurred_at); self.boot_id = boot_id
