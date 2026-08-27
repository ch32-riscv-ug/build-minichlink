# Build and release checks

[日本語](test-plan.ja.md) | [Back to README](../README.md)

Status: automated checks for the initial implementation.

## Policy

GitHub Actions publishes a release only when artifacts for all six hosts exist
and pass the checks below. The scope is the build, archives, and metadata.
Programming, terminal, debugging, and operation in any particular hardware
environment are neither tested nor guaranteed.

## Metadata

- Exactly the six expected hosts are present, with no unknown hosts.
- Every host directory contains one `build.json` and one archive.
- SHA-256 and size agree between artifacts and both generated JSON records.
- The upstream commit and commit time are recorded.
- This repository's builder commit and the build revision are recorded.
- The libusb version, URL, checksum, and linkage are recorded.
- Compiler version, flags, and dynamic dependencies are recorded per host.
- Existing version records cannot be overwritten.
- Invalid or incomplete input cannot produce a release.

## Per-host build

- Every matrix leg uses the same ch32fun commit resolved at workflow start.
- The libusb archive checksum is verified before extraction.
- Neither ch32fun nor libusb is patched.
- Release optimization is enabled and debug symbols are removed.
- The archive contains exactly one `minichlink-<version>/` root directory.
- The executable, ch32fun `LICENSE`, and libusb `COPYING` are present.
- Only Linux archives include `99-minichlink.rules`.

On native runners, confirm that `minichlink -h` exits successfully, its help
contains `-l`, and libusb is not a dynamic dependency. This is an executable
format and linkage smoke check, not a probe or target operation guarantee.

Cross-built binaries receive static format and dependency checks. Record every
unavailable execution check and its reason in the build log and `build.json`.
Windows checks should use a tool such as `objdump -p` to confirm that
`libusb-1.0.dll` is not imported and to record imported DLLs.

## Workflow

- A schedule checks the latest upstream commit and does nothing when the
  corresponding build is already published.
- An unseen upstream commit is built with revision `r1`.
- A rebuild of the same upstream commit after a build-affecting repository
  change uses the next revision after the highest published one.
- Documentation-only changes do not publish a release.
- One fully resolved SHA is passed unchanged to every matrix leg.
- Manual runs support `ref` and `dry_run` inputs.
- The matrix uses `fail-fast: false`, but no partial release is published.
- A dry run does not modify tags, releases, or the repository.
- Published tags, assets, and version records are never replaced.
- Release notes state that operation is not guaranteed.

## Release publication criteria

- All six archives and `tools_minichlink.json` exist.
- Archive, metadata, and license checks pass.
- Unavailable execution checks and their reasons are visible.
- The corresponding version record matches the release assets.
- Release notes state that artifacts carry no operation guarantee.

User hardware tests and adoption decisions are not release criteria for this
repository.
