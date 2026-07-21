from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..domain import (
    ClassificationLabel,
    ClassificationState,
    ClassificationUpdate,
    ProtocolThresholds,
)


class RssiClassifier:
    """Manual RSSI classifier with a confirmation count and hysteresis band."""

    def __init__(self, thresholds: ProtocolThresholds) -> None:
        if thresholds.state_confirmation_count < 1:
            raise ValueError("state_confirmation_count must be positive")
        if thresholds.inside_rssi_dbm <= thresholds.outside_rssi_dbm:
            raise ValueError("inside RSSI must be greater than outside RSSI")
        self.thresholds = thresholds
        self.state = ClassificationState(ClassificationLabel.UNKNOWN, None, 0, (), None)

    def _candidate(self, rssi_dbm: int) -> ClassificationLabel | None:
        if rssi_dbm >= self.thresholds.inside_rssi_dbm:
            return ClassificationLabel.INSIDE
        if rssi_dbm <= self.thresholds.outside_rssi_dbm:
            return ClassificationLabel.OUTSIDE
        return None

    def update(self, observed_at: datetime, rssi_dbm: int) -> ClassificationUpdate:
        if observed_at.tzinfo is None:
            raise ValueError("observation timestamp must be timezone-aware")
        observed_at = observed_at.astimezone(timezone.utc)
        candidate = self._candidate(rssi_dbm)
        previous = self.state.confirmed
        recent = tuple((at, value) for at, value in self.state.recent_samples if observed_at - at <= timedelta(seconds=30))
        recent += ((observed_at, rssi_dbm),)

        if candidate is None or candidate == previous:
            self.state = ClassificationState(previous, None, 0, recent, observed_at)
        elif candidate == self.state.candidate:
            count = self.state.candidate_count + 1
            if count >= self.thresholds.state_confirmation_count:
                self.state = ClassificationState(candidate, None, 0, recent, observed_at)
            else:
                self.state = ClassificationState(previous, candidate, count, recent, observed_at)
        else:
            self.state = ClassificationState(previous, candidate, 1, recent, observed_at)
        return ClassificationUpdate(previous, self.state.confirmed, previous != self.state.confirmed, rssi_dbm, observed_at, self.state)
