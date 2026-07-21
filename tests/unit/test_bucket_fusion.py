from datetime import datetime, timezone
from decimal import Decimal

from safe_kiosk_people_agent.domain import ProtocolSourceDetail, Source
from safe_kiosk_people_agent.metrics.fusion import build_bucket_metric, weighted_inside_count


def detail(count: int) -> ProtocolSourceDetail:
    return ProtocolSourceDetail(count, 0, 0, Decimal(0), Decimal(0), 0, 0, 0)


def test_one_source_is_renormalized_to_weight_one() -> None:
    assert weighted_inside_count({Source.WIFI: 3, Source.BLE: None}, {Source.WIFI: Decimal("0.4"), Source.BLE: Decimal("0.6")}) == 3


def test_dual_outage_has_no_numeric_bucket() -> None:
    metric = build_bucket_metric(datetime(2026, 1, 1, tzinfo=timezone.utc), {Source.WIFI: None, Source.BLE: None}, {Source.WIFI: detail(0), Source.BLE: detail(0)}, {Source.WIFI: Decimal(1), Source.BLE: Decimal(1)})
    assert metric is None
