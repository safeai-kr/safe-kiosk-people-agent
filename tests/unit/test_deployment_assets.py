from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_installer_exposes_phased_commands_without_reboot() -> None:
    script = (ROOT / "deploy/install.sh").read_text()
    assert "--prepare" in script
    assert "--post-reboot" in script
    assert "--verify-active" in script
    assert "systemctl reboot" not in script
    assert "shutdown" not in script
    assert "current.new" in script and "mv -Tf" in script


def test_systemd_units_use_current_release_contract() -> None:
    units = list((ROOT / "deploy/systemd").glob("*.service"))
    assert units
    for unit in units:
        text = unit.read_text()
        if "ExecStart=" in text:
            assert "/opt/safe-kiosk-people-agent/" in text
