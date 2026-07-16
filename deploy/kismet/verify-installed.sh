#!/bin/sh
set -eu
mode=${1:---package-only}
expected=$(cat "$(dirname "$0")/package-version.txt")
test "$(dpkg-query -W -f='${Version}' kismet 2>/dev/null)" = "$expected"
test "$(kismet --version 2>/dev/null | head -n1)" = "$expected"
if [ "$mode" = "--actual-uid" ]; then
  id safe-kiosk-kismet >/dev/null
  runuser -u safe-kiosk-kismet -- test -x "$(dpkg-query -L kismet-capture-linux-wifi | grep '/kismet_cap_linux_wifi$' | head -n1)"
fi
