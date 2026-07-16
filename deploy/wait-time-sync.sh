#!/bin/sh
set -eu
timedatectl show -p NTPSynchronized --value | grep -qx yes
