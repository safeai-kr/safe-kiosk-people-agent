from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .command import CommandRunner
from .locks import FileLock
from .ownership import HolderState, InterfaceOwnershipInspector
from .record import RecoveryResult


class WifiRecovery:
    def __init__(self, runner: CommandRunner | None = None, lock_path: Path | None = None, inspector: InterfaceOwnershipInspector | None = None) -> None:
        self.runner = runner or CommandRunner()
        self.lock_path = lock_path or Path("/run/lock/safe-kiosk-people-wifi.recovery")
        self.inspector = inspector or InterfaceOwnershipInspector()

    def recover(self, roles: object, now: datetime) -> RecoveryResult:
        holders = roles.get("holders", []) if isinstance(roles, dict) else []
        report = self.inspector.inspect(list(holders), expected_pids=set())
        if report.state in {HolderState.FOREIGN, HolderState.AMBIGUOUS}:
            return RecoveryResult("unavailable", report.reason or "foreign_holder", 75)
        uplink = set(roles.get("uplink_identifiers", ())) if isinstance(roles, dict) else set()
        commands = (("ip", "link", "set", "skwifi0", "down"), ("ip", "link", "set", "skwifi0", "up"))
        if any(value in uplink for command in commands for value in command):
            return RecoveryResult("unavailable", "uplink_mutation_denied", 78)
        with FileLock(self.lock_path):
            completed: list[str] = []
            for argv in commands:
                result = self.runner.run(argv, timeout_seconds=20)
                if result.returncode != 0:
                    return RecoveryResult("unavailable", "recovery_command_failed", 75, tuple(completed))
                completed.append(" ".join(argv))
        return RecoveryResult("healthy", "recovery_completed", 0, tuple(completed))
