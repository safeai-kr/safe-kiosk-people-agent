from datetime import timedelta
import pytest

PROCESS_RECOVERY_DEADLINE = timedelta(minutes=2)
INTERFACE_RECOVERY_DEADLINE = timedelta(minutes=5)

@pytest.mark.pi_fault
def test_fault_suite_requires_pi_host() -> None:
    pytest.skip("requires Raspberry Pi 5 and installed systemd bundle")

def assert_no_committed_outbox_loss(before: set[str], after: set[str]) -> None:
    assert before <= after

def assert_no_fabricated_bucket_during_dual_outage(buckets: list[object], heartbeats: int) -> None:
    assert buckets == []
    assert heartbeats > 0
