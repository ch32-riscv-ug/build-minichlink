# build-minichlink

[日本語](README.ja.md)

Build and package cross-platform binaries of
[minichlink](https://github.com/cnlohr/ch32fun/tree/master/minichlink) from a
pinned ch32fun commit. Each archive has the single-root layout required by
Arduino package indexes and other binary consumers.

> [!IMPORTANT]
> This repository is currently a pre-implementation scaffold. The release
> design and metadata generator exist, but the build script, CI workflows, and
> published releases do not yet exist.

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
                    └── versions/<version>.json
```

## Intended output

The initial design covers these Arduino host identifiers:

| Arduino `host` | Build environment | Archive |
|---|---|---|
| `x86_64-pc-linux-gnu` | native Linux x86-64 | `.tar.gz` |
| `aarch64-linux-gnu` | native Linux Arm64 | `.tar.gz` |
| `x86_64-apple-darwin` | macOS with `-arch x86_64` | `.tar.gz` |
| `arm64-apple-darwin` | native macOS Arm64 | `.tar.gz` |
| `x86_64-mingw32` | mingw-w64 cross-build | `.zip` |
| `i686-mingw32` | mingw-w64 cross-build | `.zip` |

Each archive will contain one `minichlink-<version>/` directory with the
executable and the applicable upstream license files. Linux archives will also
carry the upstream udev rules. libusb is intended to be linked statically;
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

Only [`emit_fragment.py`](emit_fragment.py), which validates per-host build
metadata and generates release records, is implemented. It is not yet wired to
a build or release workflow.

- [Initial design and decisions](docs/design.md) ([日本語](docs/design.ja.md))
- [Development and repository guide](docs/development.md) ([日本語](docs/development.ja.md))
- [Build and release checks](docs/test-plan.md) ([日本語](docs/test-plan.ja.md))
- [Third-party licenses and redistribution notes](THIRD-PARTY-NOTICE.md)

## License

[MIT](LICENSE) applies only to this repository's own code and documentation.
The generated binaries contain third-party work under separate terms; see
[THIRD-PARTY-NOTICE.md](THIRD-PARTY-NOTICE.md).
