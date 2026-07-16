from pathlib import Path
from safe_kiosk_people_agent.config import load_config
from safe_kiosk_people_agent.interfaces.render import render_nm_unmanaged_dropin
def test_networkmanager_dropin_appends_both_capture_selectors():
    assert render_nm_unmanaged_dropin(load_config(Path('tests/fixtures/config/minimal.toml')).wifi).endswith('interface-name:=skwifi0mon\n')
