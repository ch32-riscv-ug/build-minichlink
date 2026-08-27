#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=build-config.sh
source "$repo_root/build-config.sh"

host=${1:-}
case "$host" in
  x86_64-pc-linux-gnu|aarch64-linux-gnu|x86_64-apple-darwin|arm64-apple-darwin|x86_64-mingw32|i686-mingw32) ;;
  *) echo "usage: $0 <supported Arduino host>" >&2; exit 2 ;;
esac

: "${VERSION:?VERSION is required}"
: "${UPSTREAM_DIR:?UPSTREAM_DIR is required}"

if [[ ! -f "$UPSTREAM_DIR/minichlink/Makefile" || ! -f "$UPSTREAM_DIR/LICENSE" ]]; then
  echo "UPSTREAM_DIR is not a complete ch32fun checkout: $UPSTREAM_DIR" >&2
  exit 2
fi

dist_root=${DIST_DIR:-$repo_root/dist}
work_root=${WORK_DIR:-$repo_root/work}
download_root=${DOWNLOAD_DIR:-$repo_root/src/downloads}
work_dir="$work_root/$host"
dist_host="$dist_root/$host"
mkdir -p "$work_root" "$download_root" "$dist_host"
find "$work_dir" -mindepth 1 -delete 2>/dev/null || true
find "$dist_host" -mindepth 1 -delete
mkdir -p "$work_dir" "$dist_host"

libusb_archive="$download_root/libusb-${LIBUSB_VERSION}.tar.bz2"
if [[ ! -f "$libusb_archive" ]]; then
  curl --fail --location --retry 3 --output "$libusb_archive" "$LIBUSB_URL"
fi
actual_libusb_sha=$(shasum -a 256 "$libusb_archive" | awk '{print $1}')
if [[ "$actual_libusb_sha" != "$LIBUSB_SHA256" ]]; then
  echo "libusb checksum mismatch: expected $LIBUSB_SHA256, got $actual_libusb_sha" >&2
  exit 1
fi

tar -xf "$libusb_archive" -C "$work_dir"
libusb_src="$work_dir/libusb-$LIBUSB_VERSION"
libusb_build="$work_dir/libusb-build"
mkdir -p "$libusb_build"

cc=""
configure_host=()
libusb_cflags="-O2"
libusb_ldflags=""
cflags="-O2 -DNDEBUG -Wall -Wno-unused-function -DCH32V003 -DMINICHLINK -I."
ldflags=""
binary_name="minichlink"
archive_ext="tar.gz"
execution_status="skipped: cross-built binary cannot run on this runner"

case "$host" in
  x86_64-pc-linux-gnu|aarch64-linux-gnu)
    cc=gcc
    ldflags="$libusb_build/libusb/.libs/libusb-1.0.a -lpthread -ludev -Wl,-s"
    execution_status="run"
    ;;
  x86_64-apple-darwin)
    cc=cc
    configure_host=(--host=x86_64-apple-darwin)
    libusb_cflags="-arch x86_64 -O2"
    libusb_ldflags="-arch x86_64"
    cflags="-arch x86_64 -O2 -DNDEBUG -Wall -Wno-unused-function -Wno-asm-operand-widths -Wno-deprecated-declarations -Wno-deprecated-non-prototype -D__MACOSX__ -DCH32V003 -DMINICHLINK -I."
    ldflags="-arch x86_64 $libusb_build/libusb/.libs/libusb-1.0.a -lpthread -framework CoreFoundation -framework IOKit -framework Security -Wl,-x"
    ;;
  arm64-apple-darwin)
    cc=cc
    configure_host=(--host=aarch64-apple-darwin)
    libusb_cflags="-arch arm64 -O2"
    libusb_ldflags="-arch arm64"
    cflags="-arch arm64 -O2 -DNDEBUG -Wall -Wno-unused-function -Wno-asm-operand-widths -Wno-deprecated-declarations -Wno-deprecated-non-prototype -D__MACOSX__ -DCH32V003 -DMINICHLINK -I."
    ldflags="-arch arm64 $libusb_build/libusb/.libs/libusb-1.0.a -lpthread -framework CoreFoundation -framework IOKit -framework Security -Wl,-x"
    execution_status="run"
    ;;
  x86_64-mingw32)
    cc=x86_64-w64-mingw32-gcc
    configure_host=(--host=x86_64-w64-mingw32)
    cflags="-O2 -DNDEBUG -Wall -D_WIN32_WINNT=0x0600 -DCH32V003 -DMINICHLINK -I."
    ldflags="-static $libusb_build/libusb/.libs/libusb-1.0.a -lpthread -lsetupapi -lcfgmgr32 -lole32 -ladvapi32 -lws2_32 -Wl,-s"
    binary_name="minichlink.exe"
    archive_ext="zip"
    ;;
  i686-mingw32)
    cc=i686-w64-mingw32-gcc
    configure_host=(--host=i686-w64-mingw32)
    cflags="-O2 -DNDEBUG -Wall -D_WIN32_WINNT=0x0600 -DCH32V003 -DMINICHLINK -I."
    ldflags="-static $libusb_build/libusb/.libs/libusb-1.0.a -lpthread -lsetupapi -lcfgmgr32 -lole32 -ladvapi32 -lws2_32 -Wl,-s"
    binary_name="minichlink.exe"
    archive_ext="zip"
    ;;
esac

(
  cd "$libusb_build"
  CC="$cc" CFLAGS="$libusb_cflags" LDFLAGS="$libusb_ldflags" \
    "$libusb_src/configure" "${configure_host[@]}" \
      --disable-shared --enable-static --disable-udev \
      --disable-examples-build --disable-tests-build
  make -j"${BUILD_JOBS:-2}"
)

minichlink_dir="$UPSTREAM_DIR/minichlink"
source_words=$(
  make -s --no-print-directory -C "$minichlink_dir" \
    --eval 'print-c-s:;@printf "%s\n" "$(C_S)"' print-c-s
)
upstream_version=$(
  make -s --no-print-directory -C "$minichlink_dir" \
    --eval 'print-version:;@printf "%s\n" "$(VERSION)"' print-version
)
read -r -a sources <<< "$source_words"
read -r -a cflag_args <<< "$cflags"
read -r -a ldflag_args <<< "$ldflags"

binary="$work_dir/$binary_name"
(
  cd "$minichlink_dir"
  "$cc" -o "$binary" "${sources[@]}" "${cflag_args[@]}" \
    "${ldflag_args[@]}" "-DVERSION=\"$upstream_version\""
)

binary_format=$(file -b "$binary")
case "$host" in
  x86_64-pc-linux-gnu) [[ "$binary_format" == *"x86-64"* ]] ;;
  aarch64-linux-gnu) [[ "$binary_format" == *"aarch64"* || "$binary_format" == *"ARM64"* ]] ;;
  x86_64-apple-darwin) [[ "$(lipo -archs "$binary")" == "x86_64" ]] ;;
  arm64-apple-darwin) [[ "$(lipo -archs "$binary")" == "arm64" ]] ;;
  x86_64-mingw32) [[ "$binary_format" == *"PE32+"* && "$binary_format" == *"x86-64"* ]] ;;
  i686-mingw32) [[ "$binary_format" == *"PE32"* && "$binary_format" != *"PE32+"* && "$binary_format" == *"Intel 80386"* ]] ;;
esac

help_file="$work_dir/help.txt"
if [[ "$execution_status" == "run" ]]; then
  set +e
  "$binary" -h >"$help_file" 2>&1
  help_status=$?
  set -e
  grep -F -- '-l ' "$help_file" >/dev/null
  execution_status="run: minichlink -h exited $help_status and advertised -l"
fi

dependencies_file="$work_dir/dependencies.txt"
: > "$dependencies_file"
case "$host" in
  *-linux-gnu)
    readelf -d "$binary" | sed -n 's/.*Shared library: \[\(.*\)\]/\1/p' > "$dependencies_file"
    if grep -i 'libusb' "$dependencies_file"; then
      echo "Linux binary unexpectedly depends on dynamic libusb" >&2
      exit 1
    fi
    ;;
  *-apple-darwin)
    otool -L "$binary" | tail -n +2 | sed 's/^[[:space:]]*//; s/ (.*//' > "$dependencies_file"
    if grep -i 'libusb' "$dependencies_file"; then
      echo "macOS binary unexpectedly depends on dynamic libusb" >&2
      exit 1
    fi
    ;;
  *-mingw32)
    objdump_tool=${cc%-gcc}-objdump
    "$objdump_tool" -p "$binary" | sed -n 's/^[[:space:]]*DLL Name: //p' > "$dependencies_file"
    if grep -i 'libusb' "$dependencies_file"; then
      echo "Windows binary unexpectedly depends on libusb DLL" >&2
      exit 1
    fi
    ;;
esac

package_parent="$work_dir/package"
package_root="$package_parent/minichlink-$VERSION"
mkdir -p "$package_root"
cp "$binary" "$package_root/$binary_name"
cp "$UPSTREAM_DIR/LICENSE" "$package_root/LICENSE"
cp "$libusb_src/COPYING" "$package_root/COPYING"
if [[ "$host" == *-linux-gnu ]]; then
  cp "$minichlink_dir/99-minichlink.rules" "$package_root/99-minichlink.rules"
fi

archive_name="minichlink-$VERSION-$host.$archive_ext"
archive="$dist_host/$archive_name"
if [[ "$archive_ext" == "zip" ]]; then
  (cd "$package_parent" && zip -q -r "$archive" "minichlink-$VERSION")
else
  COPYFILE_DISABLE=1 tar -czf "$archive" -C "$package_parent" "minichlink-$VERSION"
fi

ARCHIVE="$archive" EXPECTED_ROOT="minichlink-$VERSION" python3 - <<'PY'
import os
import pathlib
import tarfile
import zipfile

archive = pathlib.Path(os.environ["ARCHIVE"])
if archive.suffix == ".zip":
    names = zipfile.ZipFile(archive).namelist()
else:
    names = tarfile.open(archive).getnames()
roots = {name.split("/", 1)[0] for name in names if name and name != "."}
if roots != {os.environ["EXPECTED_ROOT"]}:
    raise SystemExit(f"archive roots are {sorted(roots)}, expected one root")
PY

runner=${RUNNER_NAME:-"local-$(uname -s)-$(uname -m)"}
cc_version=$($cc --version | head -n 1)
HOST="$host" ARCHIVE_NAME="$archive_name" RUNNER="$runner" CC="$cc" \
CC_VERSION="$cc_version" CFLAGS_RECORD="$cflags" LDFLAGS_RECORD="$ldflags" \
DEPENDENCIES_FILE="$dependencies_file" EXECUTION_STATUS="$execution_status" \
  BINARY_FORMAT="$binary_format" \
python3 - "$dist_host/build.json" <<'PY'
import json
import os
import pathlib
import sys

dependencies = pathlib.Path(os.environ["DEPENDENCIES_FILE"]).read_text().splitlines()
record = {
    "host": os.environ["HOST"],
    "archiveFileName": os.environ["ARCHIVE_NAME"],
    "runner": os.environ["RUNNER"],
    "cc": os.environ["CC"],
    "ccVersion": os.environ["CC_VERSION"],
    "cflags": os.environ["CFLAGS_RECORD"],
    "ldflags": os.environ["LDFLAGS_RECORD"],
    "dynamicDependencies": dependencies,
    "binaryFormat": os.environ["BINARY_FORMAT"],
    "executionChecks": os.environ["EXECUTION_STATUS"],
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(record, indent=2) + "\n")
PY

echo "built $archive"
