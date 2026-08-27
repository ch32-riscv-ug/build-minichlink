# build・release検査

[English](test-plan.md) | [READMEへ戻る](../README.ja.md)

状態: 初版実装の自動検査要件。

## 方針

GitHub Actionsは6 hostの成果物がすべて揃い、以下の自動検査に合格した場合だけreleaseを
公開する。確認対象はbuild、archive、metadataである。実機での書き込み、terminal、debug、
特定環境での動作は検査・保証しない。

## metadata生成

- 6つのhostがすべて存在し、未知のhostが含まれないこと。
- 各host directoryに`build.json`とarchiveが1つずつあること。
- archiveのSHA-256とsizeが`tools_minichlink.json`と`versions/<version>.json`で一致すること。
- upstream commitとcommit日時が記録されること。
- このrepositoryのbuilder commitとbuild revisionが記録されること。
- libusb version、URL、checksum、link方式が記録されること。
- compiler version、flags、動的依存がhostごとに記録されること。
- 既存のversion記録を上書きしないこと。
- 入力不足や不正なmetadataではreleaseを公開しないこと。

## host別build

全hostで次を確認する。

- workflowが最初に解決した同一のch32fun commitを使用していること。
- libusb archiveのSHA-256を展開前に検証すること。
- ch32funとlibusbのsourceへpatchを当てていないこと。
- release向け最適化を行い、debug symbolを除去していること。
- archiveの直下にdirectoryが1つだけあること。
- root directory名が`minichlink-<version>`であること。
- 実行ファイル、ch32funの`LICENSE`、libusbの`COPYING`があること。
- Linux archiveだけに`99-minichlink.rules`があること。

native runnerで実行できるbinaryでは、`minichlink -h`が終了コード0になること、helpに`-l`
optionがあること、libusbが動的依存に現れないことを確認する。これは実行形式とlink結果の
smoke checkであり、probeやtargetを使った動作保証ではない。

cross-buildしたbinaryは形式と依存関係を静的に検査する。実行できない検査と理由をbuild
logと`build.json`に残す。Windowsでは`objdump -p`などを使い、`libusb-1.0.dll`を要求しない
こととimport DLLの一覧を確認する。

## workflow

- scheduleがupstreamの最新commitを確認し、該当するbuildが公開済みなら何もしないこと。
- 未releaseのupstream commitなら`r1`としてbuildすること。
- buildに影響するこのrepositoryの変更で同じupstream commitを再buildする場合、既存最大値の
  次のbuild revisionを使用すること。
- 文書だけの変更ではreleaseを作らないこと。
- 解決した完全SHAを全matrix legへ渡し、branch名をlegごとに再解決しないこと。
- 手動実行では`ref`と`dry_run`を指定できること。
- matrixは`fail-fast: false`で全hostの失敗情報を残すこと。
- 1 hostでも失敗または欠落した場合は公開しないこと。
- dry-runではtag、release、repositoryを変更しないこと。
- 公開済みtag、asset、version記録を差し替えないこと。
- release notesに動作を保証しない旨を明記すること。

## release公開の完了条件

- 6 hostすべてのarchiveと`tools_minichlink.json`がある。
- archive、metadata、licenseの自動検査がすべて成功している。
- 実行できなかった検査と理由が明示されている。
- 対応する`versions/<version>.json`がrepositoryにあり、release assetと一致する。
- release notesが成果物の動作を保証しないことを示している。

利用者による実機テストと採用判断は、このrepositoryのrelease条件に含めない。
