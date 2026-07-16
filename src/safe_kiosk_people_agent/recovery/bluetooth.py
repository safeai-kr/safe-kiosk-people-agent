from datetime import datetime
from .record import RecoveryResult
class BluetoothRecovery:
    def recover(self, identity: object, now: datetime) -> RecoveryResult:
        return RecoveryResult("recovering", "recovery_actions_not_configured", 75)
