from datetime import datetime, timezone
from pathlib import Path

from safe_kiosk_people_agent.control import CollectionControl


def test_pause_ack_is_required_before_pressure_rotation(tmp_path: Path) -> None:
    control = CollectionControl(tmp_path / "control.json")
    now = datetime.now(timezone.utc)
    pause = control.request_pause(reason="storage_full", boot_id="boot", now=now)
    for component in ("kismet", "wifi", "ble"):
        control.acknowledge(component, pause.generation)
    assert control.wait_for_ack(generation=pause.generation, required={"kismet", "wifi", "ble"}, timeout_seconds=1)
