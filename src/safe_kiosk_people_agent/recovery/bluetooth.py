from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .command import CommandRunner
from .locks import FileLock
from .ownership import HolderState, InterfaceOwnershipInspector
from .record import RecoveryResult


class BluetoothRecovery:
    def __init__(self, runner: CommandRunner | None = None, lock_path: Path | None = None, inspector: InterfaceOwnershipInspector | None = None) -> None:
        self.runner = runner or CommandRunner()
        self.lock_path = lock_path or Path("/run/lock/safe-kiosk-people-ble.recovery")
        self.inspector = inspector or InterfaceOwnershipInspector()

    def recover(self, identity: object, now: datetime) -> RecoveryResult:
        holders = identity.get("holders", []) if isinstance(identity, dict) else []
        report = self.inspector.inspect(list(holders), expected_pids=set())
        if report.state in {HolderState.FOREIGN, HolderState.AMBIGUOUS}:
            return RecoveryResult("unavailable", report.reason or "foreign_holder", 75)
        adapter = str(identity.get("adapter", "")) if isinstance(identity, dict) else ""
        if not adapter.startswith("hci"):
            return RecoveryResult("unavailable", "invalid_hci_identity", 78)
        with FileLock(self.lock_path):
            result = self.runner.run(("hciconfig", adapter, "reset"), timeout_seconds=20)
        if result.returncode != 0:
            return RecoveryResult("unavailable", "recovery_command_failed", 75)
        return RecoveryResult("healthy", "recovery_completed", 0, (f"hciconfig {adapter} reset",))
