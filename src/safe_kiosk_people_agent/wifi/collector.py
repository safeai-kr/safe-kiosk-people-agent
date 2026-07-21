from __future__ import annotations

from typing import Iterable

from ..collectors.summary import TokenizedObservation
from ..domain import KismetPacket, Source
from ..privacy import DeviceTokenizer


class WifiObservationCollector:
    def __init__(self, tokenizer: DeviceTokenizer, collector_run_id: str) -> None:
        if not collector_run_id.strip():
            raise ValueError("collector_run_id is required")
        self.tokenizer = tokenizer
        self.collector_run_id = collector_run_id

    def normalize(self, packets: Iterable[KismetPacket]) -> tuple[TokenizedObservation, ...]:
        result: list[TokenizedObservation] = []
        seen: set[tuple[str, object]] = set()
        for packet in packets:
            key = (packet.transmitter_address.lower(), packet.observed_at)
            if key in seen:
                continue
            seen.add(key)
            result.append(TokenizedObservation(
                packet.transmitter_address,
                Source.WIFI,
                self.tokenizer.token_for(Source.WIFI, packet.transmitter_address),
                packet.observed_at,
                packet.signal_dbm,
                packet.frequency_mhz,
                None,
            ))
        return tuple(result)
