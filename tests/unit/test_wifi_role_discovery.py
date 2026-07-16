from pathlib import Path
from safe_kiosk_people_agent.config import load_config
from safe_kiosk_people_agent.interfaces.discovery import HostNetworkState,WifiRoleVerifier
def test_kernel_order_never_changes_hardware_roles():
    config=load_config(Path('tests/fixtures/config/minimal.toml'))
    for name in ('boot_builtin_wlan0.json','boot_external_wlan0.json'):
        snap=WifiRoleVerifier(HostNetworkState.from_json(Path('tests/fixtures/interfaces')/name)).verify(config)
        assert snap.capture.interface=='skwifi0' and snap.uplink.permanent_mac==config.wifi.uplink_permanent_mac
