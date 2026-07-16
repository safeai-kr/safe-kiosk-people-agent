from __future__ import annotations
import hashlib
import hmac
import re
import stat
from pathlib import Path
from .domain import Source

class AddressError(ValueError): pass
class SecretError(ValueError): pass

def normalize_address(address: str) -> str:
    value = address.strip().lower().replace("-", ":")
    if not re.fullmatch(r"[0-9a-f]{2}(?::[0-9a-f]{2}){5}", value):
        raise AddressError("invalid radio address")
    return value

class DeviceTokenizer:
    def __init__(self, secret: bytes) -> None: self._secret = secret
    @classmethod
    def from_file(cls, path: Path) -> "DeviceTokenizer":
        st = path.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or stat.S_IMODE(st.st_mode) != 0o600:
            raise SecretError("secret file must be a regular mode-0600 one-link file")
        secret = path.read_bytes()
        if len(secret) < 32 or secret != secret.strip(): raise SecretError("secret must be at least 32 bytes without surrounding whitespace")
        return cls(secret)
    def token_for(self, source: Source, address: str) -> str:
        message = f"{source.value}:{normalize_address(address)}".encode()
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()
