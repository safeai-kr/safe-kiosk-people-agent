from datetime import datetime, timezone
from pathlib import Path

from safe_kiosk_people_agent.domain import ConfigSnapshot
from safe_kiosk_people_agent.storage.metrics import MetricsStore


def test_runtime_state_survives_store_restart(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    config = ConfigSnapshot(1, "threshold-v1", "digest", now, "{}")
    first = MetricsStore(tmp_path / "metrics.sqlite")
    first.initialize_runtime_state(now, config)
    second = MetricsStore(tmp_path / "metrics.sqlite")
    state = second.load_runtime_state()
    assert state is not None and state.processed_through <= now
