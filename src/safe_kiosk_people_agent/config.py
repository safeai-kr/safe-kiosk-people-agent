from __future__ import annotations

import hashlib
import json
import math
import re
import tomllib
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from enum import StrEnum
from typing import Mapping
from uuid import UUID

SUMMARY_WINDOW_SECONDS = 10
BUCKET_SECONDS = 300
BUCKET_LATENESS_SECONDS = 30
REPLAY_HORIZON_SECONDS = 86_400
WATCHDOG_PROBE_SECONDS = 20
KISMET_GENERATION_MAX_AGE_SECONDS = 43_200

class ConfigError(ValueError): pass

@dataclass(frozen=True)
class IdentityConfig:
    location_id: str
    sensor_id: UUID
    metric_version: str
    site_reference_radius_m: Decimal | None

@dataclass(frozen=True)
class WifiConfig:
    interface: str
    usb_id_path: str
    usb_sysfs_path: Path
    permanent_mac: str
    driver: str
    regulatory_country: str
    uplink_permanent_mac: str
    uplink_connection_uuid: UUID
    kismet_db_path: Path

@dataclass(frozen=True)
class BleConfig:
    adapter: str
    usb_sysfs_path: Path

@dataclass(frozen=True)
class ThresholdConfig:
    wifi_inside_rssi_dbm: int
    wifi_outside_rssi_dbm: int
    ble_inside_rssi_dbm: int
    ble_outside_rssi_dbm: int
    state_confirmation_count: int
    session_timeout_seconds: int
    min_dwell_seconds: int
    max_dwell_seconds: int
    wifi_people_weight: Decimal
    ble_people_weight: Decimal
    threshold_version: str

@dataclass(frozen=True)
class StorageConfig:
    max_state_bytes: int
    min_free_bytes: int
    kismet_max_db_bytes: int

@dataclass(frozen=True)
class UploadConfig:
    supabase_url: str
    ingest_path: str
    device_token_file: Path
    connect_timeout_seconds: float
    request_timeout_seconds: float
    upload_batch_size: int

@dataclass(frozen=True)
class RuntimeConfig:
    installation_secret_file: Path

@dataclass(frozen=True)
class AgentConfig:
    identity: IdentityConfig
    wifi: WifiConfig
    ble: BleConfig
    thresholds: ThresholdConfig
    storage: StorageConfig
    upload: UploadConfig
    runtime: RuntimeConfig

def canonical_json_value(value: object) -> object:
    if is_dataclass(value):
        return {f.name: canonical_json_value(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping): return {str(k): canonical_json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [canonical_json_value(v) for v in value]
    if isinstance(value, (UUID, Path)): return str(value)
    if isinstance(value, Decimal):
        if not value.is_finite(): raise ConfigError("non-finite Decimal")
        return format(value, "f")
    if isinstance(value, float):
        if not math.isfinite(value): raise ConfigError("non-finite float")
        return format(Decimal(str(value)), "f")
    if isinstance(value, StrEnum): return value.value
    if value is None or isinstance(value, (str, int, bool)): return value
    raise ConfigError(f"unsupported digest value: {type(value).__name__}")

def canonical_digest(value: object) -> str:
    payload = json.dumps(canonical_json_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()

def config_digest(config: AgentConfig) -> str: return canonical_digest(config)
def threshold_digest(config: ThresholdConfig) -> str: return canonical_digest(config)

_MAC = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")
_VERSION = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

def validate_config(config: AgentConfig) -> None:
    t, w, b, i = config.thresholds, config.wifi, config.ble, config.identity
    if t.max_dwell_seconds != 21_600: raise ConfigError("max_dwell_seconds must equal 21600")
    if t.min_dwell_seconds >= t.max_dwell_seconds: raise ConfigError("min_dwell_seconds must be below max_dwell_seconds")
    if not t.threshold_version or not _VERSION.fullmatch(t.threshold_version): raise ConfigError("threshold_version")
    if not (t.wifi_inside_rssi_dbm > t.wifi_outside_rssi_dbm and t.ble_inside_rssi_dbm > t.ble_outside_rssi_dbm): raise ConfigError("inside RSSI must be greater than outside RSSI")
    if t.wifi_people_weight == 0 and t.ble_people_weight == 0: raise ConfigError("at least one protocol weight must be nonzero")
    if not i.location_id or not i.metric_version: raise ConfigError("installation-specific identity is required")
    if i.site_reference_radius_m is not None and i.site_reference_radius_m <= 0: raise ConfigError("site_reference_radius_m must be positive")
    if w.interface != "skwifi0" or not _MAC.fullmatch(w.permanent_mac) or not _MAC.fullmatch(w.uplink_permanent_mac) or w.permanent_mac.lower() == w.uplink_permanent_mac.lower(): raise ConfigError("unsafe Wi-Fi role configuration")
    if not w.usb_id_path or not w.driver or not w.usb_sysfs_path.is_absolute() or len(w.regulatory_country) != 2 or not w.regulatory_country.isupper() or w.regulatory_country == "00": raise ConfigError("unsafe Wi-Fi role configuration")
    if not w.uplink_connection_uuid: raise ConfigError("uplink connection UUID")
    if not re.fullmatch(r"hci[0-9]+", b.adapter) or not b.usb_sysfs_path.is_absolute(): raise ConfigError("unsafe BLE identity")
    if not config.upload.supabase_url or config.upload.connect_timeout_seconds <= 0 or config.upload.request_timeout_seconds <= 0: raise ConfigError("upload configuration")

def _section(data: dict, name: str) -> dict: return data.get(name, {})

def load_config(path: Path) -> AgentConfig:
    with path.open("rb") as f: d = tomllib.load(f)
    i, w, b, t, s, u, r = map(lambda n: _section(d, n), ("identity","wifi","ble","thresholds","storage","upload","runtime"))
    c = AgentConfig(
      IdentityConfig(str(i["location_id"]), UUID(str(i["sensor_id"])), str(i["metric_version"]), Decimal(str(i["site_reference_radius_m"])) if i.get("site_reference_radius_m") is not None else None),
      WifiConfig(str(w.get("interface","skwifi0")), str(w["usb_id_path"]), Path(w["usb_sysfs_path"]), str(w["permanent_mac"]), str(w["driver"]), str(w["regulatory_country"]), str(w["uplink_permanent_mac"]), UUID(str(w["uplink_connection_uuid"])), Path(w.get("kismet_db_path","/var/lib/safe-kiosk-people-agent/kismet/kismet.db"))),
      BleConfig(str(b["adapter"]), Path(b["usb_sysfs_path"])),
      ThresholdConfig(int(t["wifi_inside_rssi_dbm"]), int(t["wifi_outside_rssi_dbm"]), int(t["ble_inside_rssi_dbm"]), int(t["ble_outside_rssi_dbm"]), int(t.get("state_confirmation_count",3)), int(t.get("session_timeout_seconds",600)), int(t.get("min_dwell_seconds",60)), int(t.get("max_dwell_seconds",21600)), Decimal(str(t["wifi_people_weight"])), Decimal(str(t["ble_people_weight"])), str(t["threshold_version"])),
      StorageConfig(int(s.get("max_state_bytes",2147483648)), int(s.get("min_free_bytes",1073741824)), int(s.get("kismet_max_db_bytes",1073741824))),
      UploadConfig(str(u["supabase_url"]), str(u.get("ingest_path","/functions/v1/post-location-people-metrics")), Path(u.get("device_token_file","/etc/safe-kiosk-people-agent/device-token")), float(u.get("connect_timeout_seconds",10)), float(u.get("request_timeout_seconds",30)), int(u.get("upload_batch_size",288))),
      RuntimeConfig(Path(r.get("installation_secret_file","/etc/safe-kiosk-people-agent/installation-secret"))))
    validate_config(c); return c
