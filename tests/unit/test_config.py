from dataclasses import replace
from decimal import Decimal
import pytest
from conftest import MINIMAL
from safe_kiosk_people_agent.config import ConfigError, config_digest, load_config, threshold_digest, validate_config

def test_default_policy_is_six_hours() -> None:
    config = load_config(MINIMAL)
    assert config.thresholds.state_confirmation_count == 3
    assert config.thresholds.session_timeout_seconds == 600
    assert config.thresholds.min_dwell_seconds == 60
    assert config.thresholds.max_dwell_seconds == 21_600

@pytest.mark.parametrize("invalid_max", [21_599, 21_601])
def test_six_hour_dwell_ceiling_is_invariant(invalid_max: int) -> None:
    original = load_config(MINIMAL)
    with pytest.raises(ConfigError, match="max_dwell_seconds must equal 21600"):
        validate_config(replace(original, thresholds=replace(original.thresholds, max_dwell_seconds=invalid_max)))

def test_radius_is_metadata_only_but_must_be_positive() -> None:
    original = load_config(MINIMAL)
    with pytest.raises(ConfigError, match="site_reference_radius_m"):
        validate_config(replace(original, identity=replace(original.identity, site_reference_radius_m=Decimal("0"))))

def test_threshold_version_cannot_hide_changed_content() -> None:
    original = load_config(MINIMAL).thresholds
    changed = replace(original, wifi_inside_rssi_dbm=original.wifi_inside_rssi_dbm - 1)
    assert original.threshold_version == changed.threshold_version
    assert threshold_digest(original) != threshold_digest(changed)
    assert len(threshold_digest(original)) == 64

def test_config_digest_canonicalizes_values() -> None:
    first = load_config(MINIMAL)
    assert config_digest(first) == config_digest(load_config(MINIMAL))
    assert len(config_digest(first)) == 64

def test_wifi_roles_are_bound_to_hardware_not_kernel_order() -> None:
    wifi = load_config(MINIMAL).wifi
    assert wifi.interface == "skwifi0"
    assert wifi.usb_id_path == "platform-xhci-hcd.1-usb-0:1.2:1.0"
    assert wifi.permanent_mac == "02:11:22:33:44:55"

def test_ble_runtime_identity_is_usb_path_not_hci_number() -> None:
    assert load_config(MINIMAL).ble.adapter == "hci1"

@pytest.mark.parametrize("field,value", [("interface", "wlan0"), ("regulatory_country", "00"), ("regulatory_country", "kr"), ("uplink_permanent_mac", "02:11:22:33:44:55")])
def test_unsafe_wifi_role_configuration_is_rejected(field: str, value: object) -> None:
    original = load_config(MINIMAL)
    with pytest.raises(ConfigError):
        validate_config(replace(original, wifi=replace(original.wifi, **{field: value})))
