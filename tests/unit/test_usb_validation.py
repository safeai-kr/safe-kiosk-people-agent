from pathlib import Path

import pytest

from safe_kiosk_people_agent.recovery.usb import UsbDeviceValidator, ValidatedUsbDevice


def test_usb_identity_requires_absolute_sysfs_and_matching_interface(tmp_path: Path) -> None:
    validator = UsbDeviceValidator()
    device = ValidatedUsbDevice(tmp_path / "usb", "1-1.2", "mt76x2u", "skwifi0")
    assert validator.validate_capture(device) == device
    with pytest.raises(ValueError):
        validator.validate_hci(device)
