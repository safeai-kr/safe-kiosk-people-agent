from __future__ import annotations
import json
import sys
from pathlib import Path

def main() -> int:
    report = json.loads(Path(sys.argv[1]).read_text())
    missing = {"schema_version", "status", "started_at"} - report.keys()
    if missing or report["status"] != "complete": raise SystemExit(f"invalid report: {missing}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
