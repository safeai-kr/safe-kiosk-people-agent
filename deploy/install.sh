#!/bin/sh
set -eu
PREFIX=/opt/safe-kiosk-people-agent
STATE=/var/lib/safe-kiosk-people-agent/install-state.json
PHASE=; BUNDLE=; EXPECTED_COMMIT=; EXPECTED_SHA=
usage() { echo "usage: $0 --prepare --bundle /absolute/bundle.tar.gz | --post-reboot | --verify-active --expected-commit SHA --expected-bundle-sha256 SHA" >&2; exit 64; }
while [ "$#" -gt 0 ]; do
  case "$1" in
    --prepare) PHASE=prepare; shift ;;
    --post-reboot) PHASE=post-reboot; shift ;;
    --verify-active) PHASE=verify-active; shift ;;
    --bundle) [ "$#" -ge 2 ] || usage; BUNDLE=$2; shift 2 ;;
    --expected-commit) [ "$#" -ge 2 ] || usage; EXPECTED_COMMIT=$2; shift 2 ;;
    --expected-bundle-sha256) [ "$#" -ge 2 ] || usage; EXPECTED_SHA=$2; shift 2 ;;
    *) usage ;;
  esac
done
[ -n "$PHASE" ] || usage
[ "$(id -u)" -eq 0 ] || { echo 'run as root' >&2; exit 1; }
write_state() {
  phase=$1; commit=$2; digest=$3
  install -d -m 0700 "$(dirname "$STATE")"
  tmp=${STATE}.tmp
  printf '{"phase":"%s","git_commit":"%s","bundle_sha256":"%s","manifest_digest":"%s"}\n' "$phase" "$commit" "$digest" "$digest" > "$tmp"
  sync -d "$tmp" 2>/dev/null || true
  mv -f "$tmp" "$STATE"
}
prepare() {
  case "$BUNDLE" in /*) ;; *) echo 'bundle must be absolute' >&2; exit 78 ;; esac
  [ -f "$BUNDLE" ] || { echo 'bundle not found' >&2; exit 78; }
  version=$(basename "$BUNDLE" | sed 's/^safe-kiosk-people-agent-//; s/-linux-aarch64\.tar\.gz$//')
  [ -n "$version" ] || { echo 'invalid bundle name' >&2; exit 78; }
  digest=$(sha256sum "$BUNDLE" | awk '{print $1}')
  release="$PREFIX/releases/$version"
  install -d -m 0755 "$release" "$PREFIX/releases"
  tar -xzf "$BUNDLE" -C "$release"
  ln -sfn "$release" "$PREFIX/current.new"
  mv -Tf "$PREFIX/current.new" "$PREFIX/current"
  write_state awaiting_reboot unknown "$digest"
  echo "prepared release $version; reboot is operator-controlled"
}
post_reboot() {
  [ -L "$PREFIX/current" ] || { echo 'current release is not staged' >&2; exit 75; }
  write_state active "$(git -C "$PREFIX/current" rev-parse HEAD 2>/dev/null || echo unknown)" unknown
}
verify_active() {
  [ -L "$PREFIX/current" ] || { echo 'active release missing' >&2; exit 75; }
  [ -n "$EXPECTED_COMMIT" ] && [ -n "$EXPECTED_SHA" ] || usage
  actual=$(git -C "$PREFIX/current" rev-parse HEAD 2>/dev/null || true)
  [ "$actual" = "$EXPECTED_COMMIT" ] || { echo 'commit mismatch' >&2; exit 78; }
  state_digest=$(awk -F'"bundle_sha256":"' 'NF>1 {split($2,a,"\""); print a[1]}' "$STATE" 2>/dev/null || true)
  [ "$state_digest" = "$EXPECTED_SHA" ] || { echo 'bundle digest mismatch' >&2; exit 78; }
}
case "$PHASE" in
  prepare) prepare ;;
  post-reboot) post_reboot ;;
  verify-active) verify_active ;;
esac
