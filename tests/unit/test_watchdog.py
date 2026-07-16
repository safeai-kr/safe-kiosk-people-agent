import pytest
from unittest.mock import AsyncMock, Mock
from safe_kiosk_people_agent.health.probes import ProbeResult, WatchdogLoop
@pytest.mark.asyncio
async def test_watchdog_uses_probe_progress_without_observations():
    notifier=Mock();clock=Mock();clock.boottime_ns.return_value=10_000_000_000
    await WatchdogLoop(notifier,clock).run_once(AsyncMock(return_value=ProbeResult(True,1,10_000_000_000,'idle poll committed')))
    notifier.watchdog.assert_called_once()
@pytest.mark.asyncio
async def test_readiness_waits_for_first_real_probe():
    notifier=Mock();clock=Mock();clock.boottime_ns.return_value=10_000_000_000;loop=WatchdogLoop(notifier,clock)
    assert not loop.ready
    await loop.run_once(AsyncMock(return_value=ProbeResult(True,1,10_000_000_000,'db readable')))
    assert loop.ready
