from __future__ import annotations

import json
import os
import platform
from datetime import timedelta
from pathlib import Path

import pytest

PROCESS_RECOVERY_DEADLINE = timedelta(minutes=2)
INTERFACE_RECOVERY_DEADLINE = timedelta(minutes=5)


def pi_candidate() -> dict[str, str]:
    if platform.machine() != "aarch64":
        pytest.skip("Pi fault tests are hardware-only; macOS is excluded")
    required = ("PI_CANDIDATE_SHA", "PI_BUNDLE_SHA256", "PI_TEST_ENDPOINT")
    missing = [name for name in required if not os.getenv(name)]
    state_path = Path(os.getenv("PI_INSTALL_STATE", "/var/lib/safe-kiosk-people-agent/install-state.json"))
    if missing or not state_path.exists():
        pytest.fail(f"Pi precondition missing: env={missing}, state={state_path}")
    state = json.loads(state_path.read_text())
    assert state.get("git_commit") == os.environ["PI_CANDIDATE_SHA"]
    assert state.get("bundle_sha256") == os.environ["PI_BUNDLE_SHA256"]
    return state


@pytest.mark.pi_fault
def test_fault_suite_has_explicit_pi_preconditions() -> None:
    candidate = pi_candidate()
    assert candidate["phase"] == "active"


def assert_no_committed_outbox_loss(before: set[str], after: set[str]) -> None:
    assert before <= after


def assert_no_fabricated_bucket_during_dual_outage(buckets: list[object], heartbeats: int) -> None:
    assert buckets == []
    assert heartbeats > 0
