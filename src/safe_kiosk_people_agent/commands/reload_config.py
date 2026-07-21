from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..config import ConfigError, config_digest, load_config


@dataclass(frozen=True)
class ConfigReloadResult:
    applied: bool
    reason: str
    active_generation: int
    exit_status: Literal[0, 75, 78]


class ConfigReloader:
    def __init__(self, active_path: Path) -> None:
        self.active_path = active_path
        self.generation_path = active_path.with_suffix(active_path.suffix + ".generation")

    def _generation(self) -> int:
        try:
            return int(self.generation_path.read_text().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def apply(self, candidate_path: Path) -> ConfigReloadResult:
        try:
            candidate = load_config(candidate_path)
            current = load_config(self.active_path) if self.active_path.exists() else None
        except (OSError, ConfigError, KeyError, ValueError) as exc:
            return ConfigReloadResult(False, f"invalid_candidate:{exc}", self._generation(), 78)
        if current is not None and candidate.identity != current.identity:
            return ConfigReloadResult(False, "identity_change_requires_restart", self._generation(), 78)
        generation = self._generation() + 1
        temporary = self.active_path.with_suffix(self.active_path.suffix + ".candidate")
        try:
            self.active_path.parent.mkdir(parents=True, exist_ok=True)
            data = candidate_path.read_bytes()
            with temporary.open("wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            temporary.replace(self.active_path)
            with self.generation_path.open("w") as stream:
                stream.write(str(generation)); stream.flush(); os.fsync(stream.fileno())
            directory_fd = os.open(self.active_path.parent, os.O_RDONLY)
            try: os.fsync(directory_fd)
            finally: os.close(directory_fd)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            return ConfigReloadResult(False, f"promotion_failed:{exc}", self._generation(), 75)
        return ConfigReloadResult(True, "applied", generation, 0)


def reload_config(path: Path, active_path: Path | None = None) -> dict[str, object]:
    if active_path is None:
        config = load_config(path)
        return {"applied": False, "reason": "metrics_service_acknowledgement_required", "config_digest": config_digest(config)}
    result = ConfigReloader(active_path).apply(path)
    return {"applied": result.applied, "reason": result.reason, "active_generation": result.active_generation, "exit_status": result.exit_status}
