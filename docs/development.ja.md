# 開発ガイド

[English](development.md) | [READMEへ戻る](../README.ja.md)

## 現在の構成

build、version解決、metadata生成、CI、release workflowまで実装されています。

```text
README.md                 英語の入口
README.ja.md              日本語の入口
LICENSE                   repository自身のMIT License
THIRD-PARTY-NOTICE.md     第三者著作物と再配布条件
emit_fragment.py          release fragmentとbuild記録の生成
resolve_version.py        upstream commitの解決とversion採番
build-config.sh           upstreamとlibusb入力の固定値
build.sh                  host別buildの共通入口
make_source_bundle.sh     release用source bundleの生成
.github/workflows/        CI、upstream確認、build、release
tests/                    Python scriptの単体test
versions/                 公開済みversionのbuild記録
docs/design.ja.md         初版設計、判断理由、調査結果
docs/design.md            同内容の英語版
docs/development.ja.md    repository構成と開発手順
docs/development.md       同内容の英語版
docs/test-plan.ja.md      buildとreleaseの自動検査
docs/test-plan.md         同内容の英語版
```

`dist/`と`work/`は一時成果物でありcommitしません。

## 必要なもの

metadata生成スクリプトの実行にはPython 3.10以上、または[uv](https://docs.astral.sh/uv/)が必要です。`emit_fragment.py`にはuv用のscript headerがあるため、実行権限がある環境では直接実行できます。

```sh
python3 --version
uv --version
```

compiler、libusbのbuild依存、host別toolchainは[初版仕様書](design.ja.md)の「ビルド定義」とworkflowのmatrixを正本とします。

## 手元でのbuild

対象のch32fun checkoutに対してversionを解決し、表示されたversionを`VERSION`へ設定して
host別scriptを実行します。compilerとlibrary headerは対象hostのrunnerと同じものが必要です。

```sh
python3 ./resolve_version.py \
  --upstream /path/to/ch32fun \
  --versions versions \
  --builder-sha "$(git rev-parse HEAD)" \
  --mode manual

VERSION=<表示されたversion> \
UPSTREAM_DIR=/path/to/ch32fun \
./build.sh x86_64-pc-linux-gnu
```

`build.sh`はlibusb release archiveを取得してchecksumを検証し、`dist/<host>/`へarchiveと
`build.json`を出力します。macOS 2種はそれぞれnative runnerでbuildし、Windows 2種だけを
Linuxからcross-buildします。

source bundleを手元で作る場合は、cleanでcommit済みのbuilder treeを使います。

```sh
VERSION=<表示されたversion> \
UPSTREAM_DIR=/path/to/ch32fun \
UPSTREAM_SHA="$(git -C /path/to/ch32fun rev-parse HEAD)" \
BUILDER_SHA="$(git rev-parse HEAD)" \
./make_source_bundle.sh
```

## metadata生成スクリプト

`emit_fragment.py`は各matrix legが生成した次の入力を読みます。

```text
dist/<host>/build.json
dist/<host>/<archive>
dist/<source-bundle>
```

6 hostがすべて揃い、各host directoryにarchiveが1つだけあることを検査したうえで、次を生成します。

```text
dist/tools_minichlink.json
versions/<version>.json
```

主な引数は`--help`で確認できます。

```sh
./emit_fragment.py --help
```

生成済みの`versions/<version>.json`は上書きしません。公開済みversionを差し替えないappend-only運用をscript側でも保証するためです。

## Actionsでの公開

`build.yml`は日次のupstream確認、buildに影響する`main`へのpush、手動実行で起動します。
手動実行ではch32funの`ref`と、公開を行わない`dry_run`を指定できます。6 hostがすべて成功した
場合だけdraft releaseを作り、version記録をdefault branchへcommitしてから公開します。
repositoryのbranch protectionはGitHub Actionsによるこのcommitを許可する必要があります。

## 実装時の原則

- host固有のbuild処理はworkflow YAMLではなく`build.sh <host>`へ集約し、手元でも同じ処理を実行できるようにする。
- ch32funとlibusbのsourceは変更せず、入力commit・archive・checksumを固定する。
- `dist/`のarchiveはcommitせず、公開releaseへ添付する。
- `versions/<version>.json`は公開したbuildの検証根拠としてcommitする。
- source一覧をrepository側へ複製せず、upstream Makefileから取得する。
- upstreamまたはbuild手順の変更を検出したらActionsでbuild・releaseする。
- 実機テスト、動作保証、採用判断をこのrepositoryの責務に含めない。
- 文書上の「検証済み」と「予定」を、実装やCI結果に合わせて更新する。

## 文書を変更するとき

READMEは利用者向けの概要と現在地に絞り、詳細な要件と判断理由は`design.ja.md`、実行可能な開発手順はこの文書、検証項目は`test-plan.ja.md`へ記載します。

英語版と日本語版は相互リンクし、事実関係を同じ変更で同期します。文書へ基準日や更新日を
書かず、変更時期はrepositoryの履歴で確認します。第三者著作物、link方式、同梱licenseを
変更する場合は`THIRD-PARTY-NOTICE.md`も同時に更新します。
