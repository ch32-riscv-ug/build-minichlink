# 開発ガイド

[English](development.md) | [READMEへ戻る](../README.ja.md)

## 現在の構成

このrepositoryは実装前の雛形です。現時点ではrelease metadataを生成する`emit_fragment.py`のみが実装され、build scriptとGitHub Actions workflowは未実装です。

```text
README.md                 英語の入口
README.ja.md              日本語の入口
LICENSE                   repository自身のMIT License
THIRD-PARTY-NOTICE.md     第三者著作物と再配布条件
emit_fragment.py          release fragmentとbuild記録の生成
docs/design.ja.md         初版設計、判断理由、調査結果
docs/design.md            同内容の英語版
docs/development.ja.md    repository構成と開発手順
docs/development.md       同内容の英語版
docs/test-plan.ja.md      buildとreleaseの自動検査
docs/test-plan.md         同内容の英語版
```

実装後は次の構成を追加する予定です。

```text
build.sh                  host別buildの共通入口
.github/workflows/        upstream更新確認、build、release
versions/                 公開済みversionのbuild記録
dist/                     一時成果物。commitしない
```

## 必要なもの

metadata生成スクリプトの実行にはPython 3.10以上、または[uv](https://docs.astral.sh/uv/)が必要です。`emit_fragment.py`にはuv用のscript headerがあるため、実行権限がある環境では直接実行できます。

```sh
python3 --version
uv --version
```

build実装で必要になるcompiler、libusbのbuild依存、host別toolchainは[初版仕様書](design.ja.md)の「ビルド定義」を正本とします。まだ全hostで検証されていないため、この文書では未確定のinstall commandを提示しません。

## metadata生成スクリプト

`emit_fragment.py`は各matrix legが生成した次の入力を読みます。

```text
dist/<host>/build.json
dist/<host>/<archive>
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
