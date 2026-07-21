from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ValidatedUsbDevice:
    sysfs_path: Path; usb_node: str; driver: str; current_interface: str
class UsbDeviceValidator:
    def _validate(self, device: ValidatedUsbDevice, prefix: str) -> ValidatedUsbDevice:
        if not device.sysfs_path.is_absolute() or not device.usb_node or not device.driver:
            raise ValueError("invalid USB identity")
        if not device.current_interface.startswith(prefix):
            raise ValueError("interface identity mismatch")
        return device
    def validate_capture(self, device: ValidatedUsbDevice) -> ValidatedUsbDevice: return self._validate(device, "skwifi")
    def validate_hci(self, device: ValidatedUsbDevice) -> ValidatedUsbDevice: return self._validate(device, "hci")
