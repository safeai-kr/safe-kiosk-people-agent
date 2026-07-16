from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class RecoveryResult:
    status: Literal["healthy", "recovering", "unavailable"]
    reason: str
    exit_status: Literal[0, 75, 78]
    actions_completed: tuple[str, ...] = ()
