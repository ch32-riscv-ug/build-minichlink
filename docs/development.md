# Development guide

[日本語](development.ja.md) | [Back to README](../README.md)

## Current layout

The build, version resolution, metadata generation, CI, and release workflows
are implemented.

```text
README.md / README.ja.md             English and Japanese entry points
LICENSE                              MIT License for this repository
THIRD-PARTY-NOTICE.md                third-party redistribution terms
emit_fragment.py                     release fragment and build records
resolve_version.py                   upstream resolution and version assignment
build-config.sh                      pinned upstream and libusb inputs
build.sh                             common per-host build entry point
make_source_bundle.sh                release source bundle generation
.github/workflows/                   CI, polling, build, and release
tests/                               Python script unit tests
versions/                            published build records
docs/design.md / design.ja.md        design, rationale, research
docs/development.md / development.ja.md
                                     repository and development guide
docs/test-plan.md / test-plan.ja.md  build and release checks
```

`dist/` and `work/` are temporary output and are never committed.

## Requirements

Running the metadata generator requires Python 3.10 or later, or
[uv](https://docs.astral.sh/uv/). The script has a uv script header and can be
executed directly where its executable bit is preserved.

```sh
python3 --version
uv --version
./emit_fragment.py --help
```

Compiler, libusb, and per-host toolchain requirements are defined by the
[initial design](design.md) and the workflow matrix.

## Local builds

Resolve a version against a ch32fun checkout, set `VERSION` to the value shown,
and invoke the host build script. The target host's compiler and development
headers must match those installed by the workflow matrix.

```sh
python3 ./resolve_version.py \
  --upstream /path/to/ch32fun \
  --versions versions \
  --builder-sha "$(git rev-parse HEAD)" \
  --mode manual

VERSION=<version-shown-above> \
UPSTREAM_DIR=/path/to/ch32fun \
./build.sh x86_64-pc-linux-gnu
```

`build.sh` downloads and verifies the libusb release archive, then writes an
archive and `build.json` under `dist/<host>/`. Both macOS targets build on their
respective native runners; only the two Windows targets are cross-built from
Linux.

To create the source bundle locally, use a clean, committed builder tree:

```sh
VERSION=<version-shown-above> \
UPSTREAM_DIR=/path/to/ch32fun \
UPSTREAM_SHA="$(git -C /path/to/ch32fun rev-parse HEAD)" \
BUILDER_SHA="$(git rev-parse HEAD)" \
./make_source_bundle.sh
```

## Metadata generator

`emit_fragment.py` reads one archive and one `build.json` from every host:

```text
dist/<host>/build.json
dist/<host>/<archive>
dist/<source-bundle>
```

After verifying that all six hosts are present, it writes:

```text
dist/tools_minichlink.json
versions/<version>.json
```

It refuses to overwrite an existing version record, enforcing the append-only
release policy at the script boundary.

## Actions publication

`build.yml` runs from the daily upstream check, a build-affecting push to
`main`, or a manual dispatch. Manual runs accept a ch32fun `ref` and a
non-publishing `dry_run`. Only a complete six-host build creates a draft
release; the workflow commits the version record to the default branch before
publishing the draft. Branch protection must permit that GitHub Actions commit.

## Implementation principles

- Keep host-specific build logic in `build.sh <host>`, not only in workflow
  YAML, so the same build can be reproduced locally.
- Do not patch ch32fun or libusb. Pin and record every source input.
- Attach archives to GitHub Releases; do not commit `dist/`.
- Commit `versions/<version>.json` as the verification record for a release.
- Derive source lists from the upstream Makefile instead of copying them here.
- Let Actions build and release when it detects an upstream or build-recipe
  change.
- Keep hardware testing, operational guarantees, and adoption decisions outside
  this repository's responsibilities.

## Documentation changes

README files contain the overview and current status. Design decisions belong
in `design.md`, executable development instructions here, and verification
requirements in `test-plan.md`.

Update English and Japanese documents together and keep their reciprocal links.
Do not add document baseline or update dates; use repository history to find
when a statement changed. Update `THIRD-PARTY-NOTICE.md` whenever third-party
content, linking, or bundled licenses change.
