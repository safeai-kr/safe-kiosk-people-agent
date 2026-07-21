from datetime import datetime, timezone
from pathlib import Path

from safe_kiosk_people_agent.recovery.command import CommandRunner, CompletedCommand
from safe_kiosk_people_agent.recovery.wifi import WifiRecovery


class Runner(CommandRunner):
    def __init__(self): self.commands = []
    def run(self, argv, timeout_seconds=20):
        self.commands.append(tuple(argv)); return CompletedCommand(tuple(argv), 0)


def test_wifi_recovery_does_not_mutate_uplink(tmp_path: Path) -> None:
    runner = Runner()
    result = WifiRecovery(runner, tmp_path / "lock").recover({"holders": [], "uplink_identifiers": {"uplink-mac"}}, datetime.now(timezone.utc))
    assert result.exit_status == 0
    assert all("uplink-mac" not in " ".join(command) for command in runner.commands)
