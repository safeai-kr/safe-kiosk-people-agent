from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


def check(name: str, fn: Callable[[], tuple[bool, str]]) -> dict[str, object]:
    try:
        passed, detail = fn()
    except Exception as exc:  # pragma: no cover - defensive reporting path
        passed, detail = False, f"{type(exc).__name__}: {exc}"
    return {"name": name, "passed": passed, "detail": detail}


def command_ok(argv: list[str]) -> tuple[bool, str]:
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    return result.returncode == 0, (result.stdout or result.stderr).strip()[:512]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe Kiosk post-install Pi verification")
    parser.add_argument("--state", type=Path, default=Path("/var/lib/safe-kiosk-people-agent/install-state.json"))
    parser.add_argument("--current", type=Path, default=Path("/opt/safe-kiosk-people-agent/current"))
    parser.add_argument("--expected-commit", default=os.getenv("PI_CANDIDATE_SHA", ""))
    parser.add_argument("--expected-bundle-sha256", default=os.getenv("PI_BUNDLE_SHA256", ""))
    parser.add_argument("--output", type=Path, default=Path("/var/lib/safe-kiosk-people-agent/post-install-report.json"))
    args = parser.parse_args(argv)
    report: dict[str, object] = {"schema_version": 1, "started_at": datetime.now(timezone.utc).isoformat(), "checks": []}
    if platform.machine() != "aarch64":
        report["status"] = "precondition_failed"
        report["reason"] = "aarch64 Raspberry Pi required"
        print(json.dumps(report, sort_keys=True))
        return 78
    if os.getenv("ALLOW_PI_POST_INSTALL") != "1":
        report["status"] = "precondition_failed"
        report["reason"] = "ALLOW_PI_POST_INSTALL=1 required"
        print(json.dumps(report, sort_keys=True))
        return 78

    checks = report["checks"]
    assert isinstance(checks, list)
    checks.append(check("install_state_exists", lambda: (args.state.is_file(), str(args.state))))
    checks.append(check("current_symlink", lambda: (args.current.is_symlink(), str(args.current))))

    def state_values() -> dict[str, object]:
        return json.loads(args.state.read_text())

    checks.append(check("install_phase_active", lambda: (state_values().get("phase") == "active", str(state_values().get("phase")))))
    if args.expected_commit:
        checks.append(check("expected_commit", lambda: (state_values().get("git_commit") == args.expected_commit, str(state_values().get("git_commit")))))
    if args.expected_bundle_sha256:
        checks.append(check("expected_bundle_sha256", lambda: (state_values().get("bundle_sha256") == args.expected_bundle_sha256, str(state_values().get("bundle_sha256")))))
    checks.append(check("systemd_target", lambda: command_ok(["systemctl", "is-active", "safe-kiosk-people-agent.target"])))
    checks.append(check("capture_interface", lambda: command_ok(["ip", "link", "show", "skwifi0"])))
    checks.append(check("kismet_loopback", lambda: command_ok(["sh", "-c", "ss -ltn | grep -E '127\\.0\\.0\\.1:2501|::1:2501'"])))
    checks.append(check("wifi_spool", lambda: (any(args.current.glob("**/*wifi*.sqlite")), "wifi spool present")))
    checks.append(check("metrics_outbox", lambda: (any(args.current.glob("**/*metrics*.sqlite")), "metrics database present")))
    checks.append(check("status_endpoint", lambda: command_ok(["systemctl", "is-active", "safe-kiosk-people-metrics.service"])))
    report["status"] = "complete" if all(bool(item["passed"]) for item in checks) else "failed"
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
