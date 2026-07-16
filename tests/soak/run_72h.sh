#!/bin/sh
set -eu
duration=${1:-72}
out=${2:-/var/lib/safe-kiosk-people-agent/soak/72h-report.json}
mkdir -p "$(dirname "$out")"
python3 - "$out" "$duration" <<'PY'
import json, pathlib, sys, time
out, hours = sys.argv[1], int(sys.argv[2])
data = {"schema_version": 1, "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "duration_hours": hours, "status": "running"}
pathlib.Path(out).write_text(json.dumps(data) + "\n")
time.sleep(hours * 3600)
data["status"] = "complete"
pathlib.Path(out).write_text(json.dumps(data) + "\n")
PY
