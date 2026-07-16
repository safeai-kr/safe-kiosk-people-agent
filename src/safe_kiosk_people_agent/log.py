from __future__ import annotations
import logging
import re

class RedactionError(ValueError): pass
_FORBIDDEN = re.compile(r"(mac|address|device_token|installation_secret|device_token_header|session_id)", re.I)

def safe_log(message: str, **fields: object) -> None:
    if any(_FORBIDDEN.fullmatch(k) for k in fields): raise RedactionError("identifier fields are forbidden in structured logs")
    text = message + " " + " ".join(f"{k}={v}" for k,v in fields.items())
    if _FORBIDDEN.search(text): raise RedactionError("identifier values are forbidden in logs")
    logging.getLogger("safe_kiosk_people_agent").info(message, extra=fields)
