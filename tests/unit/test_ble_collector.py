from datetime import datetime, timezone
from safe_kiosk_people_agent.ble.collector import BleObservationCollector, parse_advertisement
from safe_kiosk_people_agent.privacy import DeviceTokenizer

def test_parse_and_tokenize_ble_advertisement() -> None:
    at=datetime(2026,1,1,tzinfo=timezone.utc)
    ad=parse_advertisement('LE Advertising Report  AA:BB:CC:DD:EE:FF RSSI: -61 dBm',at)
    assert ad and ad.rssi_dbm == -61
    values=BleObservationCollector(DeviceTokenizer(b'x'*32),'run-1').normalize([ad,ad])
    assert len(values)==1 and values[0].source.value == 'ble'

def test_parser_rejects_incomplete_line() -> None:
    assert parse_advertisement('AA:BB:CC:DD:EE:FF') is None
