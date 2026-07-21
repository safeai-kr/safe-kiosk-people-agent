from datetime import datetime, timezone

from safe_kiosk_people_agent.recovery.wifi import WifiRecovery
from safe_kiosk_people_agent.recovery.command import CommandRunner, CompletedCommand


class Runner(CommandRunner):
    def __init__(self): self.commands = []
    def run(self, argv, timeout_seconds=20):
        self.commands.append(tuple(argv)); return CompletedCommand(tuple(argv), 0)


def test_recovery_commands_do_not_include_uplink_identifier(tmp_path):
    runner = Runner()
    WifiRecovery(runner, tmp_path / "lock").recover({"holders": [], "uplink_identifiers": {"d8:3a:dd:11:22:33"}}, datetime.now(timezone.utc))
    assert all("d8:3a:dd:11:22:33" not in " ".join(command) for command in runner.commands)
