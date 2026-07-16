#!/bin/sh
set -eu
case "${1:-}" in
  --start) test "${ALLOW_TEST_REBOOT:-}" = 1 || { echo 'explicit test authorization required' >&2; exit 78; } ;;
  --status|--cleanup) : ;;
  *) echo "usage: $0 --start|--status|--cleanup" >&2; exit 64 ;;
esac
echo "Pi-only role-cycle harness"
