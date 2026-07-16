from datetime import datetime, timezone
from pathlib import Path
from safe_kiosk_people_agent.storage.maintenance import StorageMaintainer
def test_storage_pressure_requests_pause(tmp_path:Path):
    result=StorageMaintainer(tmp_path/'control.json').run_once(datetime.now(timezone.utc),free_bytes=900_000_000)
    assert result.collection_allowed is False and result.status_flag=='storage_full'
