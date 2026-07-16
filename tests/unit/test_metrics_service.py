import asyncio
from datetime import datetime, timezone
from safe_kiosk_people_agent.domain import Source, SourceHealth
from safe_kiosk_people_agent.metrics import MetricsWorker
from safe_kiosk_people_agent.metrics.service import MetricsService
from safe_kiosk_people_agent.domain import NewObservationSummary
def summary(source,token,rssi):
    at=datetime(2026,1,1,12,3,tzinfo=timezone.utc)
    return NewObservationSummary(f'{source}-{token}',source,'run',token,at,at,at,at,1,rssi,rssi,None,None)
def test_service_keeps_ble_when_wifi_unavailable():
    worker=MetricsWorker({s:__import__('safe_kiosk_people_agent.domain',fromlist=['ProtocolThresholds']).ProtocolThresholds(s,-70,-85,3) for s in (Source.WIFI,Source.BLE)})
    service=MetricsService(worker,lambda:[summary(Source.BLE,'b',-60)])
    service.record_health(Source.WIFI,SourceHealth.UNAVAILABLE,datetime.now(timezone.utc))
    buckets,quality=asyncio.run(service.run_once())
    assert buckets[0].estimated_people_count==1 and 'wifi_unavailable' in quality
