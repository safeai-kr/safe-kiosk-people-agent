#!/bin/sh
set -eu
exec python3 tests/post_install/verify.py "$@"
