from datetime import datetime, timedelta, timezone

from safe_kiosk_people_agent.domain import ClassificationLabel, ProtocolThresholds, Source
from safe_kiosk_people_agent.metrics.classifier import RssiClassifier


def test_classifier_requires_confirmation_and_keeps_hysteresis() -> None:
    classifier = RssiClassifier(ProtocolThresholds(Source.WIFI, -55, -80, 3))
    at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert classifier.update(at, -50).current is ClassificationLabel.UNKNOWN
    assert classifier.update(at + timedelta(seconds=1), -50).current is ClassificationLabel.UNKNOWN
    assert classifier.update(at + timedelta(seconds=2), -50).current is ClassificationLabel.INSIDE
    assert classifier.update(at + timedelta(seconds=3), -70).current is ClassificationLabel.INSIDE


def test_classifier_outside_confirmation() -> None:
    classifier = RssiClassifier(ProtocolThresholds(Source.BLE, -60, -85, 2))
    at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    classifier.update(at, -90)
    assert classifier.update(at + timedelta(seconds=1), -90).current is ClassificationLabel.OUTSIDE
