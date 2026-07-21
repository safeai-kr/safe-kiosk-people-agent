from datetime import datetime, timezone

from safe_kiosk_people_agent.domain import KismetPacket
from safe_kiosk_people_agent.privacy import DeviceTokenizer
from safe_kiosk_people_agent.wifi.collector import WifiObservationCollector


def test_wifi_normalization_never_returns_raw_address_as_token() -> None:
    packet = KismetPacket("g", 1, 1, 0, datetime.now(timezone.utc), "aa:bb:cc:dd:ee:ff", -50, 2412.0, frozenset())
    [observation] = WifiObservationCollector(DeviceTokenizer(b"x" * 32), "run").normalize([packet])
    assert observation.device_token != packet.transmitter_address
    assert packet.transmitter_address not in observation.device_token
