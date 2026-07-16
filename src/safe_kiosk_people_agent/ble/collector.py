from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Iterable
from ..domain import Source
from ..privacy import DeviceTokenizer
from ..collectors.summary import TokenizedObservation

_ADDR=re.compile(r'(?i)\b([0-9a-f]{2}(?::[0-9a-f]{2}){5})\b')
_RSSI=re.compile(r'(?i)\bRSSI\s*[:=]\s*(-?\d+)\s*d?Bm?\b|\b(-?\d+)\s*dBm\b')
@dataclass(frozen=True)
class BleAdvertisement:
    address:str; rssi_dbm:int; observed_at:datetime; tx_power_dbm:int|None=None

def parse_advertisement(line:str, observed_at:datetime|None=None) -> BleAdvertisement|None:
    address=_ADDR.search(line)
    match=_RSSI.search(line)
    if not address or not match: return None
    rssi=int(match.group(1) or match.group(2))
    return BleAdvertisement(address.group(1),rssi,observed_at or datetime.now(timezone.utc))

class BleObservationCollector:
    def __init__(self, tokenizer:DeviceTokenizer, collector_run_id:str) -> None:
        if not collector_run_id.strip(): raise ValueError('collector_run_id is required')
        self.tokenizer=tokenizer; self.collector_run_id=collector_run_id
    def normalize(self, advertisements:Iterable[BleAdvertisement]) -> tuple[TokenizedObservation,...]:
        result=[]; seen:set[tuple[str,datetime]] = set()
        for ad in advertisements:
            at=ad.observed_at.astimezone(timezone.utc)
            key=(ad.address.lower(),at)
            if key in seen: continue
            seen.add(key)
            result.append(TokenizedObservation(ad.address,Source.BLE,self.tokenizer.token_for(Source.BLE,ad.address),at,ad.rssi_dbm,None,ad.tx_power_dbm))
        return tuple(result)
