from datetime import datetime, timedelta, timezone
from threading import Event
from safe_kiosk_people_agent.ble import BleAdvertisement, BleCollectorWorker, BleObservationCollector
from safe_kiosk_people_agent.privacy import DeviceTokenizer

def test_ble_worker_flushes_summaries() -> None:
    at=[datetime(2026,1,1,tzinfo=timezone.utc)]
    def clock(): return at[0]
    ad=BleAdvertisement('aa:bb:cc:dd:ee:ff',-50,at[0])
    worker=BleCollectorWorker(BleObservationCollector(DeviceTokenizer(b'x'*32),'run'),lambda:[ad],clock=clock)
    at[0]+=timedelta(seconds=11)
    result=worker.run(Event(),max_cycles=2)
    assert result.cycles==2 and result.health.value=='healthy'

def test_ble_worker_latches_degraded_on_source_error() -> None:
    worker=BleCollectorWorker(BleObservationCollector(DeviceTokenizer(b'x'*32),'run'),lambda: (_ for _ in ()).throw(RuntimeError()))
    result=worker.run(Event(),max_cycles=1)
    assert result.health.value=='degraded'
