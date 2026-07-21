#!/usr/bin/env python3
"""Post-install smoke checks for a real Raspberry Pi deployment.

Run on the Pi with ``ALLOW_PI_POST_INSTALL=1``.  The command never mutates
services or interfaces; it only records evidence in a JSON report.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import time
from pathlib import Path


def check(name: str, fn, checks: list[dict[str, object]]) -> None:
    try:
        value = fn()
        checks.append({"name": name, "ok": bool(value), "detail": str(value)})
    except Exception as exc:  # noqa: BLE001 - report every failed probe
        checks.append({"name": name, "ok": False, "detail": f"{type(exc).__name__}: {exc}"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-commit")
    parser.add_argument("--expected-bundle-sha256")
    parser.add_argument("--state", type=Path, default=Path("/var/lib/safe-kiosk-people-agent/install-state.json"))
    parser.add_argument("--current", type=Path, default=Path("/opt/safe-kiosk-people-agent/current"))
    args = parser.parse_args()
    checks: list[dict[str, object]] = []
    check("aarch64", lambda: platform.machine() == "aarch64", checks)
    check("explicit_authorization", lambda: os.environ.get("ALLOW_PI_POST_INSTALL") == "1", checks)
    check("install_state", lambda: args.state.is_file(), checks)
    check("current_release", lambda: args.current.is_symlink() and args.current.exists(), checks)

    def state_value(key: str) -> str:
        return str(json.loads(args.state.read_text())[key])

    check("active_state", lambda: state_value("phase") == "active", checks)
    if args.expected_bundle_sha256:
        check("bundle_digest", lambda: state_value("bundle_sha256") == args.expected_bundle_sha256, checks)
    if args.expected_commit:
        check("commit", lambda: state_value("git_commit") == args.expected_commit or (args.current / "COMMIT").read_text().strip() == args.expected_commit, checks)

    units = ("safe-kiosk-people-kismet.service", "safe-kiosk-people-wifi.service", "safe-kiosk-people-ble.service", "safe-kiosk-people-metrics.service")
    for unit in units:
        check(f"unit:{unit}", lambda unit=unit: subprocess.run(("systemctl", "is-active", "--quiet", unit), check=False).returncode == 0, checks)
    check("interfaces", lambda: subprocess.run(("ip", "-brief", "link"), check=False, capture_output=True, text=True).returncode == 0, checks)
    check("kismet_loopback", lambda: subprocess.run(("curl", "-fsS", "http://127.0.0.1:2501/system/status.json"), check=False, timeout=5).returncode == 0, checks)
    report = {"schema_version": 1, "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status": "complete" if all(bool(item["ok"]) for item in checks) else "failed", "checks": checks}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
