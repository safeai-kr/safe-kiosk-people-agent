import fcntl
from pathlib import Path

class FileLock:
    def __init__(self, path: Path): self.path = path; self._fd = None
    def __enter__(self):
        self._fd = self.path.open("a+")
        fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX)
        return self
    def __exit__(self, *_):
        if self._fd: fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN); self._fd.close()
