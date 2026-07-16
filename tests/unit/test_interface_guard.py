import pytest
from safe_kiosk_people_agent.interfaces.guard import deny_uplink_mutation
def test_uplink_mutation_is_denied():
    with pytest.raises(PermissionError): deny_uplink_mutation(['nmcli','d8:3a:dd:11:22:33'],{'d8:3a:dd:11:22:33'})
