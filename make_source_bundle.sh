#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=build-config.sh
source "$repo_root/build-config.sh"

: "${VERSION:?VERSION is required}"
: "${UPSTREAM_DIR:?UPSTREAM_DIR is required}"
: "${BUILDER_SHA:?BUILDER_SHA is required}"

dist_root=${DIST_DIR:-$repo_root/dist}
download_root=${DOWNLOAD_DIR:-$repo_root/src/downloads}
work_root=${WORK_DIR:-$repo_root/work}
bundle_work="$work_root/source-bundle"
bundle_root="$bundle_work/minichlink-$VERSION-sources"
mkdir -p "$dist_root" "$download_root" "$work_root"
find "$bundle_work" -mindepth 1 -delete 2>/dev/null || true
mkdir -p "$bundle_root/ch32fun" "$bundle_root/builder"

libusb_archive="$download_root/libusb-${LIBUSB_VERSION}.tar.bz2"
if [[ ! -f "$libusb_archive" ]]; then
  curl --fail --location --retry 3 --output "$libusb_archive" "$LIBUSB_URL"
fi
actual_libusb_sha=$(shasum -a 256 "$libusb_archive" | awk '{print $1}')
if [[ "$actual_libusb_sha" != "$LIBUSB_SHA256" ]]; then
  echo "libusb checksum mismatch: expected $LIBUSB_SHA256, got $actual_libusb_sha" >&2
  exit 1
fi

git -C "$UPSTREAM_DIR" archive HEAD | tar -xf - -C "$bundle_root/ch32fun"
cp "$libusb_archive" "$bundle_root/"
cp "$repo_root/build.sh" "$repo_root/build-config.sh" \
  "$repo_root/THIRD-PARTY-NOTICE.md" "$bundle_root/builder/"
git -C "$UPSTREAM_DIR" rev-parse HEAD > "$bundle_root/UPSTREAM-COMMIT"
printf '%s\n' "$BUILDER_SHA" > "$bundle_root/BUILDER-COMMIT"

archive="$dist_root/minichlink-$VERSION-sources.tar.gz"
COPYFILE_DISABLE=1 tar -czf "$archive" -C "$bundle_work" "minichlink-$VERSION-sources"
echo "built $archive"
