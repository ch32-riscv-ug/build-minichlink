# build-minichlink

[日本語](README.ja.md)

Build and package cross-platform binaries of
[minichlink](https://github.com/cnlohr/ch32fun/tree/master/minichlink) from a
pinned ch32fun commit. Each archive has the single-root layout required by
Arduino package indexes and other binary consumers.

> [!IMPORTANT]
> The build, metadata, CI, and release workflows are implemented. See
> [Actions](https://github.com/ch32-riscv-ug/build-minichlink/actions) for the
> latest run and [Releases](https://github.com/ch32-riscv-ug/build-minichlink/releases)
> for published outputs.

This is an independent packaging project. It is not part of, affiliated with,
or endorsed by ch32fun, CNLohr, or libusb. It is also not a mirror: ch32fun
does not publish the host binaries needed here, so this project builds them in
public CI from source.

```text
pinned ch32fun commit
        + pinned libusb release
                    │
                    ▼
             public CI build
                    │
                    ├── one archive per host
                    ├── tools_minichlink.json
                    ├── corresponding source bundle
                    └── versions/<version>.json
```

## Intended output

The initial design covers these Arduino host identifiers:

| Arduino `host` | Build environment | Archive |
|---|---|---|
| `x86_64-pc-linux-gnu` | native Linux x86-64 | `.tar.gz` |
| `aarch64-linux-gnu` | native Linux Arm64 | `.tar.gz` |
| `x86_64-apple-darwin` | native Intel macOS | `.tar.gz` |
| `arm64-apple-darwin` | native macOS Arm64 | `.tar.gz` |
| `x86_64-mingw32` | mingw-w64 cross-build | `.zip` |
| `i686-mingw32` | mingw-w64 cross-build | `.zip` |

Each archive contains one `minichlink-<version>/` directory with the
executable and the applicable upstream license files. Linux archives will also
carry the upstream udev rules. Each release also carries the exact ch32fun
source, original libusb source archive, and builder scripts in a source bundle.
libusb is linked statically;
Linux will still depend dynamically on libudev because minichlink itself uses
it.

Version names identify the upstream commit:

```text
YYYY.M.D-g<short-sha>-r<build-revision>
example: 2026.8.24-g6c4dd53-r1
```

When GitHub Actions detects an upstream or build-recipe change, it builds and
publishes a GitHub Release. This repository is responsible only for building,
packaging, automated artifact checks, and publication. Hardware testing,
fitness decisions, and adoption belong to consumers.

```text
change detected -> build and automated checks -> GitHub Release
```

Publication means only that the build and packaging checks passed; it does not
guarantee operation on hardware. Releases are append-only. A build record
preserves the source commit, build revision, libusb archive checksum, compiler,
flags, dynamic dependencies, and output checksums for every host.

## Current status and documentation

The end-to-end build and release path is implemented. Linux x86-64/Arm64 builds
have run in GitHub Actions, and Windows x86-64/i686 builds have been exercised
locally in isolated environments. See the [design's validation status](docs/design.md#existing-research)
and the current Actions run for the remaining host checks.

- [Initial design and decisions](docs/design.md) ([日本語](docs/design.ja.md))
- [Development and repository guide](docs/development.md) ([日本語](docs/development.ja.md))
- [Build and release checks](docs/test-plan.md) ([日本語](docs/test-plan.ja.md))
- [Third-party licenses and redistribution notes](THIRD-PARTY-NOTICE.md)

## License

[MIT](LICENSE) applies only to this repository's own code and documentation.
The generated binaries contain third-party work under separate terms; see
[THIRD-PARTY-NOTICE.md](THIRD-PARTY-NOTICE.md).
