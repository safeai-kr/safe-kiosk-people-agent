from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Protocol

from .config import AgentConfig
from .health.systemd import SystemdNotifier


class RuntimeComponent(Protocol):
    async def open(self) -> None: ...
    async def probe(self) -> None: ...
    async def run(self, stop: asyncio.Event) -> None: ...
    async def close(self) -> None: ...
    def notify_ready(self) -> None: ...


@dataclass
class ConfiguredComponent:
    """Small lifecycle adapter used by the process entrypoints.

    Collector implementations are injected by later runtime tasks. Keeping
    this boundary dependency-free means a CLI invocation can be validated on
    macOS without trying to open Raspberry Pi-only interfaces.
    """

    name: str
    config: AgentConfig
    notifier: SystemdNotifier
    runner: Callable[[asyncio.Event], Awaitable[None]] | None = None

    async def open(self) -> None:
        return None

    async def probe(self) -> None:
        return None

    def notify_ready(self) -> None:
        self.notifier.ready(f"{self.name} ready")

    async def run(self, stop: asyncio.Event) -> None:
        if self.runner is not None:
            await self.runner(stop)
            return
        await stop.wait()

    async def close(self) -> None:
        return None


def _build(name: str, config: AgentConfig) -> RuntimeComponent:
    return ConfiguredComponent(name, config, SystemdNotifier())


def build_kismet_component(config: AgentConfig) -> RuntimeComponent:
    return _build("kismet", config)


def build_wifi_component(config: AgentConfig) -> RuntimeComponent:
    return _build("wifi", config)


def build_ble_component(config: AgentConfig) -> RuntimeComponent:
    return _build("ble", config)


def build_metrics_component(config: AgentConfig) -> RuntimeComponent:
    return _build("metrics", config)


async def serve_component(component: RuntimeComponent, stop: asyncio.Event) -> int:
    await component.open()
    try:
        await component.probe()
        component.notify_ready()
        await component.run(stop)
        return 0
    finally:
        await component.close()


def config_path(value: str | Path) -> Path:
    return value if isinstance(value, Path) else Path(value)
