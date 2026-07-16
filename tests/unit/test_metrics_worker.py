from datetime import datetime, timezone
from safe_kiosk_people_agent.domain import NewObservationSummary, Source, ProtocolThresholds
from safe_kiosk_people_agent.metrics import MetricsWorker
def summary(source,token,rssi):
    at=datetime(2026,1,1,12,3,tzinfo=timezone.utc)
    return NewObservationSummary(f'{source}-{token}',source,'run',token,at,at,at,at,1,rssi,rssi,None,None)
def test_metrics_worker_fuses_sources_in_bucket():
    t={s:ProtocolThresholds(s,-70,-85,3) for s in (Source.WIFI,Source.BLE)}
    result=MetricsWorker(t).reduce([summary(Source.WIFI,'a',-60),summary(Source.BLE,'b',-65),summary(Source.WIFI,'a',-55)])
    assert result[0].estimated_people_count==2 and result[0].observation_count==3
