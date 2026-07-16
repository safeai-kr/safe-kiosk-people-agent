from dataclasses import dataclass
import subprocess
from typing import Sequence

@dataclass(frozen=True)
class CompletedCommand:
    argv: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""

class CommandRunner:
    def run(self, argv: Sequence[str], timeout_seconds: float = 20) -> CompletedCommand:
        completed = subprocess.run(list(argv), shell=False, capture_output=True, text=True, timeout=timeout_seconds, check=False)
        return CompletedCommand(tuple(argv), completed.returncode, completed.stdout, completed.stderr)
