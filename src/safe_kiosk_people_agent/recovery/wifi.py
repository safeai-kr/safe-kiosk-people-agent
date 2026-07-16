from datetime import datetime
from .record import RecoveryResult
class WifiRecovery:
    def recover(self, roles: object, now: datetime) -> RecoveryResult:
        return RecoveryResult("recovering", "recovery_actions_not_configured", 75)
