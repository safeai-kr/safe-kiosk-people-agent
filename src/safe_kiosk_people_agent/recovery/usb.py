from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ValidatedUsbDevice:
    sysfs_path: Path; usb_node: str; driver: str; current_interface: str
class UsbDeviceValidator:
    def validate_capture(self, device: ValidatedUsbDevice) -> ValidatedUsbDevice: return device
    def validate_hci(self, device: ValidatedUsbDevice) -> ValidatedUsbDevice: return device
