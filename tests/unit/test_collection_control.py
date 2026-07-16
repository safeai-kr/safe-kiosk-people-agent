from datetime import datetime, timezone
from pathlib import Path
from safe_kiosk_people_agent.control import CollectionControl
def test_collection_generation_increases(tmp_path:Path):
    control=CollectionControl(tmp_path/'state.json'); now=datetime.now(timezone.utc)
    first=control.request_pause(reason='storage_full',boot_id='b',now=now); second=control.request_resume(reason='operator',boot_id='b',now=now)
    assert first.generation==1 and second.generation==2 and control.read().state=='resume_requested'
