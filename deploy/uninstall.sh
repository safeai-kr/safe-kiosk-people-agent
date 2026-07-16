#!/bin/sh
set -eu
systemctl disable --now safe-kiosk-people-agent.target 2>/dev/null || true
rm -f /etc/systemd/system/safe-kiosk-people-*.service /etc/systemd/system/safe-kiosk-people-agent.*
systemctl daemon-reload
