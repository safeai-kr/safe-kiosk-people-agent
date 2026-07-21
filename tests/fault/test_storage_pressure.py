from datetime import datetime, timezone

from safe_kiosk_people_agent.storage.maintenance import StorageMaintainer


def test_storage_pressure_never_deletes_without_pause_ack(tmp_path):
    result = StorageMaintainer(tmp_path / "control.json").run_once(datetime.now(timezone.utc), free_bytes=1)
    assert result.collection_allowed is False
    assert result.rows_deleted == {}
