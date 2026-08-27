# build-minichlink initial design

[日本語](design.ja.md)

Status: pre-implementation initial design. Items requiring implementation
validation are listed under [Open validation work](#open-validation-work).

## Purpose and scope

Build [minichlink](https://github.com/cnlohr/ch32fun/tree/master/minichlink)
for each supported host and publish it in a form installable as an Arduino Board
Manager tool. ArduinoCore-CH32 is the first consumer, but the output is not
Arduino-specific.

This is a build project rather than a mirror. Upstream does not publish the
required host binaries, so there is no upstream binary checksum to preserve.
The verifiable input is instead a fully resolved source commit and a recorded
build recipe.

In scope:

- per-host builds from one upstream commit resolved by the workflow;
- static libusb linking;
- archives with exactly one root directory;
- an Arduino tool fragment, `tools_minichlink.json`;
- GitHub Releases and a reproducible record for every published build; and
- automated publication when an upstream update is detected.

Out of scope:

- patches or feature development in minichlink;
- claims that a build guarantees minichlink behavior;
- automatic movement of a consumer's pinned version; and
- shared-library builds of minichlink.

## Release artifacts

Every `v<version>` release contains six host archives and one
`tools_minichlink.json`. Archives are attached to releases, not committed.

```text
minichlink-<version>/
├── minichlink              (minichlink.exe on Windows)
├── LICENSE                 ch32fun
├── COPYING                 libusb
└── 99-minichlink.rules     Linux only
```

Linux and macOS use `.tar.gz`; Windows uses `.zip`. Installing the Linux archive
does not activate its udev rules. The consumer must document that separate
system administration step.

## Versioning

minichlink does not publish a conventional project version. This repository
names a build from the upstream committer date in UTC and short commit ID:

```text
YYYY.M.D-g<short-sha>-r<build-revision>
example: 2026.8.24-g6c4dd53-r1
```

Numeric date fields have no leading zero. Different commits on the same day
remain distinct because of the SHA. The build revision starts at `r1` and is
incremented when the same upstream commit is rebuilt after a build-recipe or
dependency change. Identical source and build inputs are not published twice.
Published tags and assets are append-only.

## Hosts

| Arduino `host` | Runner and compiler |
|---|---|
| `x86_64-pc-linux-gnu` | native `gcc` on Linux x86-64 |
| `aarch64-linux-gnu` | native `gcc` on Linux Arm64 |
| `x86_64-apple-darwin` | macOS `cc -arch x86_64` |
| `arm64-apple-darwin` | native macOS Arm64 `cc` |
| `x86_64-mingw32` | `x86_64-w64-mingw32-gcc` |
| `i686-mingw32` | `i686-w64-mingw32-gcc` |

All six entries are required because a missing matching tool system can fail an
Arduino platform installation rather than merely disabling that tool.

## Build definition

### libusb

All hosts statically link a checksum-pinned upstream libusb release archive.
The initial input is libusb 1.0.29. Build it with shared libraries, examples,
tests, and libusb's optional udev integration disabled. Each macOS host is built
for one architecture; a universal static library is unnecessary.

Linux still dynamically links libudev because minichlink's ESP32-S2 backend
uses libudev directly. Removing it would require an upstream source change.

### minichlink

Use release optimization and strip debug information. Linux and macOS can
override the upstream Makefile flags. The Windows recipe hard-codes an x86-64
compiler, so the build script must derive the upstream source list and invoke
the selected mingw-w64 compiler directly. Do not copy the source list into this
repository.

The entire ch32fun repository is required because minichlink includes files
outside its own directory.

### Local build entry point

Put host branching in `build.sh <host>` so CI and local reproduction share the
same implementation. Each invocation writes one archive and one `build.json`
under `dist/<host>/`.

## Build acceptance checks

Before publication, validate archive structure, required license files, the
presence of `-l` in minichlink help, and dynamic dependencies. Record the help
exit status rather than requiring zero (upstream currently returns 255 after
displaying help). Execute the binary on native runners. For cross-builds,
perform static checks and explicitly record which execution checks were skipped.

These checks establish build and packaging integrity only. Hardware operation
is outside this repository's acceptance criteria and is not guaranteed.

## Workflow and release policy

The scheduled workflow checks the upstream default branch. When the latest
commit has not been released, it resolves that commit once, builds every host,
and publishes a GitHub Release after all automated checks pass. It may skip
intermediate commits observed between polling runs.

Manual `workflow_dispatch` supports a `ref` and a non-publishing `dry_run`.
Concurrent publication is prohibited, matrix failures do not hide other host
results, and a partial six-host release is never published.

Release notes state that artifacts are build outputs and carry no hardware
operation guarantee. A published release is immutable: do not move its tag,
replace its assets, or delete older releases.

## Responsibility boundary

Publication means only that build, archive, and metadata checks passed:

```text
upstream or build-recipe change
    -> GitHub Actions build and automated checks
    -> GitHub Release
```

Hardware testing, fitness for a consumer's requirements, pin management, and
adoption decisions belong to users. When a build-recipe or dependency fix
requires rebuilding the same upstream commit, increment the build revision and
publish a new release. Never replace the earlier version.

## Build record

`emit_fragment.py` generates `versions/<version>.json`. It records the full
upstream commit and commit time, this repository's builder commit, build
revision, libusb version/URL/checksum/linkage, per-host artifact
URL/name/SHA-256/size, runner, compiler version, flags, and dynamic dependencies.
Existing records cannot be overwritten.

## Licensing

The repository's own files are MIT. ch32fun is MIT and its `LICENSE` is bundled.
libusb is LGPL-2.1-or-later and its `COPYING` is bundled.

Because libusb is statically linked, the first distribution must satisfy the
conditions of LGPL-2.1 section 6, including an effective way for recipients to
relink with a modified library and the applicable source or object-code
provision requirements. Reproducibility metadata helps, but is not by itself a
substitute for those license requirements. See
[THIRD-PARTY-NOTICE.md](../THIRD-PARTY-NOTICE.md).

## Open validation work

- Validate static libusb and binary dependencies on macOS, Windows, and Linux
  Arm64.
- Determine exact Windows system libraries for x86-64 and i686.
- Confirm the LGPL source/object-code distribution mechanism before the first
  release.
- Choose the upstream polling interval.
- Define how Actions commits `versions/<version>.json` to the default branch,
  including permissions and the order of commit, tag, and release creation.
- Define whether libusb updates remain an explicit manual dependency change.
- Update the consumer ADR to describe this build repository and its trust model.

## Existing research

Linux x86-64 experiments have confirmed a static libusb build, the remaining
direct libudev dependency, release-size reduction after stripping, the `-l`
option, and the need for the full ch32fun checkout. Other host builds and actual
programming/debugging remain unverified. The commit history records when these
findings were added or changed.

## References

- [ch32fun](https://github.com/cnlohr/ch32fun)
- [upstream minichlink workflow](https://github.com/cnlohr/ch32fun/blob/master/.github/workflows/minichlink.yml)
- [Arduino package index specification](https://arduino.github.io/arduino-cli/latest/package_index_json-specification/)
- [ArduinoCore-CH32 ADR-0011](https://github.com/ch32-riscv-ug/ArduinoCore-CH32/blob/main/docs/adr/0011-tool-mirror-repository.ja.md)
