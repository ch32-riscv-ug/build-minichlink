# build-minichlink

[English](README.md)

[minichlink](https://github.com/cnlohr/ch32fun/tree/master/minichlink)を、固定したch32funのcommitからhostごとにビルドし、Arduino package indexなどから導入できる単一root構造のアーカイブにするプロジェクトです。

> [!IMPORTANT]
> 現在は実装前の雛形です。初版設計とrelease metadata生成スクリプトはありますが、build script、CI workflow、公開済みreleaseはまだありません。

本プロジェクトはch32fun、CNLohr、libusbとは独立しており、提携・推奨・支援を受けたものではありません。また、upstream成果物のミラーでもありません。ch32funはここで必要なhost別バイナリを公開していないため、固定したsourceから公開CIでビルドします。

```text
固定したch32fun commit
        + 固定したlibusb release
                    │
                    ▼
               公開CIでbuild
                    │
                    ├── hostごとのarchive
                    ├── tools_minichlink.json
                    └── versions/<version>.json
```

## 作成するもの

初版ではArduinoの次のhost識別子を対象とします。

| Arduino `host` | build環境 | archive |
|---|---|---|
| `x86_64-pc-linux-gnu` | Linux x86-64 native | `.tar.gz` |
| `aarch64-linux-gnu` | Linux Arm64 native | `.tar.gz` |
| `x86_64-apple-darwin` | macOS、`-arch x86_64` | `.tar.gz` |
| `arm64-apple-darwin` | macOS Arm64 native | `.tar.gz` |
| `x86_64-mingw32` | mingw-w64 cross-build | `.zip` |
| `i686-mingw32` | mingw-w64 cross-build | `.zip` |

各archiveは`minichlink-<version>/`というroot directoryを1つだけ持ち、実行ファイルと適用されるupstreamのlicense文書を収録します。Linux版にはupstreamのudev rulesも同梱します。

libusbはstatic linkする方針です。利用環境にlibusbを別途導入する必要はありません。ただしLinuxでは、minichlink自身がlibudevを直接利用するため、`libudev.so.1`への動的依存が残ります。

versionはupstream commitを識別できる次の形式です。

```text
YYYY.M.D-g<short-sha>-r<build-revision>
例: 2026.8.24-g6c4dd53-r1
```

GitHub Actionsがupstreamまたはbuild手順の変更を検出したら、buildしてGitHub Releaseへ公開します。このrepositoryが行うのはbuild、梱包、自動検査、公開までです。実機テスト、動作保証、採用判断は利用者側の責任です。

```text
変更検出 → build・自動検査 → GitHub Release
```

各releaseではsource commit、build revision、libusb archiveのchecksum、hostごとのcompilerとflags、動的依存、成果物checksumを記録します。releaseの公開はbuildと梱包が自動検査を通過したことだけを示し、実機での動作を保証しません。

## 現在の状態と関連文書

現在実装されているのは、hostごとのbuild metadataを検査し、release記録を生成する[`emit_fragment.py`](emit_fragment.py)だけです。buildやrelease workflowにはまだ接続されていません。

初版の要件、判断理由、互換性調査は[docs/design.ja.md](docs/design.ja.md)、repositoryの構成と開発手順は[docs/development.ja.md](docs/development.ja.md)、buildとreleaseの自動検査は[docs/test-plan.ja.md](docs/test-plan.ja.md)にあります。各文書には英語版へのリンクがあります。第三者著作物と再配布条件は[THIRD-PARTY-NOTICE.md](THIRD-PARTY-NOTICE.md)を参照してください。

## 利用上の注意

- 本プロジェクトはminichlink自体へpatchを当てません。機能や動作の問題はupstreamへ、build・梱包・metadataの問題はこちらへ報告してください。
- archive内のudev rulesは、installしただけではsystemへ適用されません。導入方法の案内は利用側のpackageで行う必要があります。
- 成果物はbuild済みバイナリとして提供しますが、実機での書き込みやdebug動作は保証しません。

## ライセンス

repository直下の[MIT License](LICENSE)は、このrepository自身のcodeと文書だけに適用されます。生成するバイナリには別条件の第三者著作物が含まれます。詳細は[THIRD-PARTY-NOTICE.md](THIRD-PARTY-NOTICE.md)を参照してください。
