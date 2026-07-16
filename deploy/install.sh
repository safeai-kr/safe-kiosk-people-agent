#!/bin/sh
set -eu
test "$(id -u)" -eq 0 || { echo 'run as root' >&2; exit 1; }
install -d -m 0755 /etc/safe-kiosk-people-agent
install -m 0640 deploy/config/config.toml.example /etc/safe-kiosk-people-agent/config.toml.example
systemd-sysusers deploy/sysusers.d/safe-kiosk-people-agent.conf
systemd-tmpfiles --create deploy/tmpfiles.d/safe-kiosk-people-agent.conf
install -m 0644 deploy/systemd/*.service deploy/systemd/*.target deploy/systemd/*.slice /etc/systemd/system/
systemctl daemon-reload
