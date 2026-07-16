from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import shutil
import psutil  # type: ignore[import-untyped]
@dataclass(frozen=True)
class ResourceSnapshot: cpu_percent:Decimal; memory_bytes:int; disk_free_bytes:int; checked_at:datetime
def read_resources(path:Path)->ResourceSnapshot:
    return ResourceSnapshot(Decimal(str(max(0,min(100,psutil.cpu_percent(None))))),max(0,psutil.virtual_memory().used),max(0,shutil.disk_usage(path).free),datetime.now().astimezone())
