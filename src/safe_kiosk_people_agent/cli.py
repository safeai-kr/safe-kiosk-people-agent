from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .commands.check_config import check_config
from .commands.inspect_signals import inspect_signals
from .commands.reload_config import reload_config
from .config import ConfigError


def _config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="people-agent")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check-config")
    _config_argument(check)

    inspect = commands.add_parser("inspect-signals")
    inspect.add_argument("--source", choices=("wifi", "ble", "both"), default="both")
    inspect.add_argument("--window-seconds", type=int, default=300)
    inspect.add_argument("--format", choices=("text", "json"), default="text")

    reload_parser = commands.add_parser("reload-config")
    reload_parser.add_argument("--candidate", type=Path, required=True)

    for name in ("run-kismet", "run-wifi", "run-ble", "run-metrics"):
        worker = commands.add_parser(name)
        _config_argument(worker)

    recover = commands.add_parser("recover")
    _config_argument(recover)
    recover.add_argument("--scope", choices=("wifi", "ble"), required=True)

    verify = commands.add_parser("verify-interface-roles")
    _config_argument(verify)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def parse_worker_args(
    program: str, argv: Sequence[str] | None = None
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=program)
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args(argv)


def parse_recovery_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="safe-kiosk-people-recover")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--scope", choices=("wifi", "ble"), required=True)
    return parser.parse_args(argv)


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "check-config":
        print(json.dumps(check_config(args.config), sort_keys=True))
        return 0
    if args.command == "inspect-signals":
        result = inspect_signals(args.source, args.window_seconds, args.format)
        print(json.dumps(result, sort_keys=True) if args.format == "json" else result)
        return 0
    if args.command == "reload-config":
        print(json.dumps(reload_config(args.candidate), sort_keys=True))
        return 0
    if args.command == "verify-interface-roles":
        # The privileged host snapshot is supplied by the interface-guard
        # service on Raspberry Pi. CLI validation still catches bad config.
        check_config(args.config)
        return 0
    if args.command == "recover":
        from .entrypoints import run_recovery

        return run_recovery(args.config, args.scope)

    from . import entrypoints

    handlers = {
        "run-kismet": entrypoints.run_kismet,
        "run-wifi": entrypoints.run_wifi,
        "run-ble": entrypoints.run_ble,
        "run-metrics": entrypoints.run_metrics,
    }
    handler = handlers[args.command]
    return entrypoints._run_worker(handler, args.config)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return _dispatch(parse_args(argv))
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 78
    except (FileNotFoundError, OSError) as exc:
        print(f"dependency unavailable: {exc}", file=sys.stderr)
        return 75


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
