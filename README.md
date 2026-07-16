# Safe Kiosk People Agent

Raspberry Pi 5 deployment for Wi-Fi/BLE collection and five-minute metrics aggregation.
Kismet is an operating-system dependency pinned to `2025-09-R1`.

Validate on a clean detached Pi checkout: host, Kismet package, two-phase install,
standalone probe, then target activation. Use `pytest -m pi_fault` for controlled
faults and `tests/soak/run_72h.sh` for the 72-hour report. The role-cycle harness is
test-only and requires explicit operator authorization before any reboot.
