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

    def inspect(self, holders: list[Mapping[str, object]], *, expected_pids: set[int] | None = None, helper_lock_contended: bool = False) -> OwnershipReport:
        expected = expected_pids or set()
        expected_found: list[int] = []
        foreign: list[int] = []
        defunct = False
        for holder in holders:
            state = self.classify(holder)
            pid = int(str(holder.get("pid", 0) or 0))
            if state is HolderState.DEFUNCT:
                defunct = True
            elif pid in expected or state is HolderState.EXPECTED:
                expected_found.append(pid)
            elif state is HolderState.FOREIGN:
                foreign.append(pid)
        if helper_lock_contended or foreign:
            return OwnershipReport(HolderState.FOREIGN, tuple(expected_found), tuple(foreign), helper_lock_contended, "foreign_holder")
        if len(expected_found) > 1:
            return OwnershipReport(HolderState.AMBIGUOUS, tuple(expected_found), (), False, "multiple_expected_holders")
        if expected_found:
            return OwnershipReport(HolderState.EXPECTED, tuple(expected_found), (), False, "expected_holder")
        if defunct:
            return OwnershipReport(HolderState.DEFUNCT, (), (), False, "zombie_holder")
        return OwnershipReport(HolderState.NONE)
