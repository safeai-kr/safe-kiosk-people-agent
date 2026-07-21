import asyncio

import pytest

from safe_kiosk_people_agent.runtime import serve_component


class FakeRuntime:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def open(self) -> None:
        self.calls.append("open")

    async def probe(self) -> None:
        self.calls.append("probe")

    def notify_ready(self) -> None:
        self.calls.append("ready")

    async def run(self, stop: asyncio.Event) -> None:
        self.calls.append("run")

    async def close(self) -> None:
        self.calls.append("close")


@pytest.mark.asyncio
async def test_ready_follows_open_and_probe() -> None:
    stop = asyncio.Event()
    stop.set()
    runtime = FakeRuntime()
    assert await serve_component(runtime, stop) == 0
    assert runtime.calls == ["open", "probe", "ready", "run", "close"]
