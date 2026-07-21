from __future__ import annotations

import asyncio
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Literal, Sequence

from .config import load_config
from .recovery.coordinator import RecoveryCoordinator
from .runtime import (
    build_ble_component,
    build_kismet_component,
    build_metrics_component,
    build_wifi_component,
    serve_component,
)


async def run_with_signals(
    handler: Callable[[Path, asyncio.Event], Awaitable[int]], config_path: Path
) -> int:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_stop() -> None:
        stop.set()

    for signum in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(signum, request_stop)
        except (NotImplementedError, RuntimeError):
            # Windows and embedded event loops may not expose signal handlers.
            pass
    return await handler(config_path, stop)


async def run_kismet(config_path: Path, stop: asyncio.Event) -> int:
    config = load_config(config_path)
    return await serve_component(build_kismet_component(config), stop)


async def run_wifi(config_path: Path, stop: asyncio.Event) -> int:
    config = load_config(config_path)
    return await serve_component(build_wifi_component(config), stop)


async def run_ble(config_path: Path, stop: asyncio.Event) -> int:
    config = load_config(config_path)
    return await serve_component(build_ble_component(config), stop)


async def run_metrics(config_path: Path, stop: asyncio.Event) -> int:
    config = load_config(config_path)
    return await serve_component(build_metrics_component(config), stop)


def _run_worker(
    handler: Callable[[Path, asyncio.Event], Awaitable[int]], config_path: Path
) -> int:
    return asyncio.run(run_with_signals(handler, config_path))


def main_kismet(argv: Sequence[str] | None = None) -> int:
    from .cli import parse_worker_args

    args = parse_worker_args("safe-kiosk-people-kismet", argv)
    return _run_worker(run_kismet, args.config)


def main_wifi(argv: Sequence[str] | None = None) -> int:
    from .cli import parse_worker_args

    args = parse_worker_args("safe-kiosk-people-wifi", argv)
    return _run_worker(run_wifi, args.config)


def main_ble(argv: Sequence[str] | None = None) -> int:
    from .cli import parse_worker_args

    args = parse_worker_args("safe-kiosk-people-ble", argv)
    return _run_worker(run_ble, args.config)


def main_metrics(argv: Sequence[str] | None = None) -> int:
    from .cli import parse_worker_args

    args = parse_worker_args("safe-kiosk-people-metrics", argv)
    return _run_worker(run_metrics, args.config)


def run_recovery(config_path: Path, scope: Literal["wifi", "ble"]) -> int:
    # Loading config is intentional: recovery must never run against an
    # unvalidated or partially written installation configuration.
    load_config(config_path)
    result = RecoveryCoordinator().recover(scope, datetime.now(timezone.utc))
    return int(result.exit_status)


def main_recover(argv: Sequence[str] | None = None) -> int:
    from .cli import parse_recovery_args

    args = parse_recovery_args(argv)
    return run_recovery(args.config, args.scope)
