#!/usr/bin/env -S uv run --no-project --script
# /// script
# requires-python = ">=3.10"
# ///
"""
Turn the per-host build outputs into a release's metadata.

This file is the CH32 RISC-V User Group's own work, under the repository's root
MIT LICENSE. The binaries it describes are not: they are minichlink (ch32fun,
MIT) statically linked with libusb (LGPL-2.1-or-later), and the root LICENSE
does not apply to them. See THIRD-PARTY-NOTICE.md.
このファイルは我々の著作物でルートのMIT。記述対象のバイナリはch32funとlibusbの
著作物であり、ルートのMITは適用されない。

Run by GitHub Actions (.github/workflows/build.yml); the workflow creates the
release and commits the record. This script only produces files.
GitHub Actions から実行される。release 作成と commit はワークフローが行う。

Input:  dist/<host>/<archive>  and  dist/<host>/build.json  from each matrix leg
Output: dist/tools_minichlink.json   Arduino tool definition fragment
        versions/<version>.json      the record committed to this repository

Why a record per version / versionごとに記録を残す理由:
  ch32fun publishes no release binaries, so there is no upstream checksum to
  compare against. What makes a build checkable is the recipe: the upstream
  commit, the libusb tarball and its checksum, and the compiler and flags used
  on every host. All of it goes in the record so a third party can rebuild.
  upstream にリリースバイナリが無く、照合すべき checksum が存在しない。
  照合の対象はビルド手順そのものなので、commit・libusb・フラグを全て記録する。
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

TOOL_NAME = "minichlink"
# Order matters only for readability; arduino-cli matches by host regex.
# 並びは可読性のためだけ。arduino-cli は host の正規表現で照合する。
HOST_ORDER = (
    "x86_64-pc-linux-gnu",
    "aarch64-linux-gnu",
    "x86_64-apple-darwin",
    "arm64-apple-darwin",
    "x86_64-mingw32",
    "i686-mingw32",
)

COMMENT = (
    "minichlink {version} tool definition, from the ch32-riscv-ug/build-minichlink "
    "release of the same version - do not hand-edit; take a fresh copy when adopting a "
    "new version. Unlike a mirror, these binaries have no upstream counterpart to "
    "compare against: ch32fun publishes no release assets. They are built by that "
    "repository's CI from upstream commit {sha}, build revision r{revision}, using "
    "builder commit {builder}, with libusb {libusb} linked statically. The build "
    "recipe and per-host flags are recorded in "
    "versions/{version}.json there. These artifacts are build outputs only; hardware "
    "operation is not guaranteed and consumers make their own adoption decisions."
)


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(dist: pathlib.Path) -> dict:
    """One entry per host directory, from the build.json each leg wrote."""
    found = {}
    for host_dir in sorted(p for p in dist.iterdir() if p.is_dir()):
        record = host_dir / "build.json"
        if not record.exists():
            raise SystemExit(f"{host_dir} has no build.json - did that leg fail?")
        info = json.loads(record.read_text(encoding="utf-8"))
        archives = [p for p in host_dir.iterdir() if p.name != "build.json"]
        if len(archives) != 1:
            raise SystemExit(
                f"{host_dir} holds {len(archives)} archives; expected exactly one"
            )
        info["_archive"] = archives[0]
        found[info["host"]] = info

    missing = [h for h in HOST_ORDER if h not in found]
    if missing:
        # A host with no entry fails the whole platform install, not just the
        # tool, so a partial release is worse than no release.
        # entry の無い host は platform ごと install に失敗する。欠けたまま出さない。
        raise SystemExit("no build for: " + ", ".join(missing))
    unexpected = [h for h in found if h not in HOST_ORDER]
    if unexpected:
        raise SystemExit("unexpected host(s): " + ", ".join(unexpected))
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="e.g. 2026.8.24-g6c4dd53-r1")
    ap.add_argument("--upstream-sha", required=True)
    ap.add_argument("--upstream-date", required=True, help="commit date, ISO 8601 UTC")
    ap.add_argument("--builder-sha", required=True, help="commit of this repository")
    ap.add_argument("--build-revision", required=True, type=int, help="1 for r1")
    ap.add_argument("--libusb-version", required=True)
    ap.add_argument("--libusb-sha256", required=True)
    ap.add_argument("--repo", required=True, help="owner/name of this repository")
    ap.add_argument("--dist", default="dist", type=pathlib.Path)
    ap.add_argument("--versions", default="versions", type=pathlib.Path)
    args = ap.parse_args()

    if args.build_revision < 1:
        ap.error("--build-revision must be at least 1")
    if not re.search(rf"-r{args.build_revision}$", args.version):
        ap.error("--version suffix must match --build-revision")

    found = collect(args.dist)
    base = f"https://github.com/{args.repo}/releases/download/v{args.version}"

    systems, builds = [], []
    for host in HOST_ORDER:
        info = found[host]
        archive = info["_archive"]
        systems.append(
            {
                "host": host,
                "url": f"{base}/{archive.name}",
                "archiveFileName": archive.name,
                "checksum": "SHA-256:" + sha256(archive),
                "size": str(archive.stat().st_size),
            }
        )
        builds.append(
            {
                "host": host,
                "archiveFileName": archive.name,
                "runner": info["runner"],
                "cc": info["cc"],
                "ccVersion": info["ccVersion"],
                "cflags": info["cflags"],
                "ldflags": info["ldflags"],
                "dynamicDependencies": info["dynamicDependencies"],
            }
        )

    fragment = {
        "comment": COMMENT.format(
            version=args.version,
            sha=args.upstream_sha,
            revision=args.build_revision,
            builder=args.builder_sha,
            libusb=args.libusb_version,
        ),
        "name": TOOL_NAME,
        "version": args.version,
        "upstreamRepository": "https://github.com/cnlohr/ch32fun",
        "upstreamCommit": args.upstream_sha,
        "builderCommit": args.builder_sha,
        "buildRevision": args.build_revision,
        "systems": systems,
    }
    out = args.dist / "tools_minichlink.json"
    out.write_text(json.dumps(fragment, indent=2) + "\n", encoding="utf-8")

    record = dict(fragment)
    record.pop("comment")
    record["upstreamCommittedAt"] = args.upstream_date
    record["libusb"] = {
        "version": args.libusb_version,
        "checksum": "SHA-256:" + args.libusb_sha256,
        "url": (
            f"https://github.com/libusb/libusb/releases/download/"
            f"v{args.libusb_version}/libusb-{args.libusb_version}.tar.bz2"
        ),
        "linkage": "static",
    }
    record["builds"] = builds
    args.versions.mkdir(parents=True, exist_ok=True)
    path = args.versions / f"{args.version}.json"
    if path.exists():
        # Append-only. A published version's record never changes: a consumer
        # that pinned it must keep getting the same bytes.
        # append-only。公開済み version の記録は書き換えない。
        raise SystemExit(f"{path} already exists; refusing to overwrite")
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {out} and {path}")
    for s in systems:
        print(f"  {s['host']:<22} {s['size']:>9} bytes  {s['archiveFileName']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
