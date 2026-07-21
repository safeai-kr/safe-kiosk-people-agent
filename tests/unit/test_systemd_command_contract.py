from pathlib import Path
import shlex

from safe_kiosk_people_agent.cli import parse_args


ROOT = Path(__file__).parents[2]


def test_systemd_execstart_commands_are_cli_parseable() -> None:
    for path in sorted((ROOT / "deploy/systemd").glob("safe-kiosk-people-*.service")):
        for line in path.read_text().splitlines():
            if not line.startswith("ExecStart="):
                continue
            command = shlex.split(line.removeprefix("ExecStart=").replace("%i", "wifi"))
            if command[-1].endswith(".sh"):
                continue
            executable = Path(command[0]).name
            if executable == "people-agent":
                assert parse_args(command[1:]).command in {
                    "check-config", "run-kismet", "run-wifi", "run-ble", "run-metrics", "recover"
                }
            else:
                from safe_kiosk_people_agent.cli import parse_worker_args

                assert parse_worker_args(executable, command[1:]).config.name == "config.toml"
