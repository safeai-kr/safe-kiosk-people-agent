from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

class HolderState(StrEnum): NONE="none"; EXPECTED="expected"; DEFUNCT="defunct"; FOREIGN="foreign"; AMBIGUOUS="ambiguous"
@dataclass(frozen=True)
class OwnershipReport:
    state: HolderState; expected_pids: tuple[int,...]=(); foreign_pids: tuple[int,...]=(); helper_lock_contended: bool=False; reason: str|None=None
class InterfaceOwnershipInspector:
    def classify(self, process: Mapping[str, object]) -> HolderState:
        if str(process.get("state", "")) == "Z": return HolderState.DEFUNCT
        if not process.get("pid"): return HolderState.NONE
        return HolderState.EXPECTED if bool(process.get("expected", False)) else HolderState.FOREIGN
