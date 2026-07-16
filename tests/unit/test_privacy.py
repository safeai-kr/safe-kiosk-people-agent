from pathlib import Path
import pytest
from safe_kiosk_people_agent.domain import Source
from safe_kiosk_people_agent.privacy import DeviceTokenizer, SecretError, normalize_address

def test_protocol_is_part_of_local_token(tmp_path: Path) -> None:
    path = tmp_path / "secret"; path.write_bytes(b"x"*32); path.chmod(0o600)
    tokenizer = DeviceTokenizer.from_file(path)
    assert tokenizer.token_for(Source.WIFI, "AA:BB:CC:DD:EE:FF") != tokenizer.token_for(Source.BLE, "AA:BB:CC:DD:EE:FF")
    assert len(tokenizer.token_for(Source.WIFI, "AA:BB:CC:DD:EE:FF")) == 64

def test_normalize_address() -> None:
    assert normalize_address(" AA-BB-CC-DD-EE-FF ") == "aa:bb:cc:dd:ee:ff"
    with pytest.raises(ValueError): normalize_address("not-an-address")

def test_secret_file_policy(tmp_path: Path) -> None:
    path = tmp_path / "secret"; path.write_bytes(b"x"*32); path.chmod(0o644)
    with pytest.raises(SecretError): DeviceTokenizer.from_file(path)
