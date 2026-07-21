from pathlib import Path

from safe_kiosk_people_agent.cli import parse_args, parse_worker_args


CONFIG = "/etc/safe-kiosk-people-agent/config.toml"


def test_dispatch_parser_accepts_service_commands() -> None:
    commands = (
        ["run-kismet", "--config", CONFIG],
        ["recover", "--config", CONFIG, "--scope", "wifi"],
        ["recover", "--config", CONFIG, "--scope", "ble"],
        ["verify-interface-roles", "--config", CONFIG],
        ["check-config", "--config", CONFIG],
    )
    assert [parse_args(command).command for command in commands] == [
        "run-kismet",
        "recover",
        "recover",
        "verify-interface-roles",
        "check-config",
    ]


def test_worker_argv_requires_config() -> None:
    assert parse_worker_args("safe-kiosk-people-wifi", ["--config", CONFIG]).config == Path(CONFIG)
    assert parse_worker_args("safe-kiosk-people-ble", ["--config", CONFIG]).config == Path(CONFIG)
    assert parse_worker_args("safe-kiosk-people-metrics", ["--config", CONFIG]).config == Path(CONFIG)
