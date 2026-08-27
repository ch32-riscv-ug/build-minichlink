# Development guide

[日本語](development.ja.md) | [Back to README](../README.md)

## Current layout

This repository is a pre-implementation scaffold. `emit_fragment.py`, the
release metadata generator, is currently the only implemented component. The
build script and GitHub Actions workflows do not exist yet.

```text
README.md / README.ja.md             English and Japanese entry points
LICENSE                              MIT License for this repository
THIRD-PARTY-NOTICE.md                third-party redistribution terms
emit_fragment.py                     release fragment and build records
docs/design.md / design.ja.md        design, rationale, research
docs/development.md / development.ja.md
                                     repository and development guide
docs/test-plan.md / test-plan.ja.md  build and release checks
```

The implementation is expected to add:

```text
build.sh                  common host build entry point
.github/workflows/        upstream polling, build, and release workflows
versions/                 records for published builds
dist/                     temporary output; never committed
```

## Requirements

Running the metadata generator requires Python 3.10 or later, or
[uv](https://docs.astral.sh/uv/). The script has a uv script header and can be
executed directly where its executable bit is preserved.

```sh
python3 --version
uv --version
./emit_fragment.py --help
```

Compiler, libusb, and per-host toolchain requirements remain defined by the
[initial design](design.md). This guide intentionally does not prescribe
unverified installation commands.

## Metadata generator

`emit_fragment.py` reads one archive and one `build.json` from every host:

```text
dist/<host>/build.json
dist/<host>/<archive>
```

After verifying that all six hosts are present, it writes:

```text
dist/tools_minichlink.json
versions/<version>.json
```

It refuses to overwrite an existing version record, enforcing the append-only
release policy at the script boundary.

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
