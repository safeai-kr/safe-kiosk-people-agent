from datetime import datetime, timezone
from pathlib import Path
from safe_kiosk_people_agent.domain import NewObservationSummary, Source, SourceHealth, SourceWatermark
from safe_kiosk_people_agent.storage.spool import WifiSpool

def summary() -> NewObservationSummary:
    t=datetime(2026,7,14,12,0,tzinfo=timezone.utc)
    return NewObservationSummary('s1',Source.WIFI,'run','t'*64,t,t.replace(second=10),t,t,1,-60,-60,None,None)
def watermark() -> SourceWatermark:
    t=datetime(2026,7,14,12,0,tzinfo=timezone.utc)
    return SourceWatermark(Source.WIFI,'run','boot',t,t,1,SourceHealth.HEALTHY,t,1,1)
def test_spool_append_and_read_are_sequence_based(tmp_path: Path) -> None:
    spool=WifiSpool(tmp_path/'wifi.sqlite'); [row]=spool.append_poll('g',None, [summary()], watermark()) # type: ignore[arg-type]
    assert spool.read_after(0,10)==(row,)
    assert spool.read_after(row.spool_sequence,10)==()
