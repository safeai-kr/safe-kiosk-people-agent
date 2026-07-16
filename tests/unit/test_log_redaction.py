import pytest
from safe_kiosk_people_agent.log import RedactionError, safe_log
def test_structured_log_rejects_identifier_keys() -> None:
    with pytest.raises(RedactionError): safe_log("seen", mac="AA:BB:CC:DD:EE:FF")
