# build-minichlink 初版仕様書

[English](design.md)

状態: 初版設計(実装前)。実装時の確認事項は[§11](#11-実装時の確認事項)。

## 1. 目的

[minichlink](https://github.com/cnlohr/ch32fun/tree/master/minichlink)を
hostごとにビルドし、Arduino Board Managerのtoolとしてinstallできる形で公開する。

最初の利用者は[ArduinoCore-CH32](https://github.com/ch32-riscv-ug/ArduinoCore-CH32)だが、
Arduino専用の作りにはしない。決まったhost向けにすぐ動くminichlinkが要るconsumerなら
何でも使える。

### なぜ必要か

`arduino-cli`はtoolをhostごとに1アーカイブでinstallし、各アーカイブに**単一の
rootディレクトリ**を要求する。minichlinkはどちらも満たさない。

- **upstreamはhost別のreleaseバイナリを公開していない。** 一方、開発は`master`で続いている
- したがって**ミラーは成立しない**。転送すべき成果物が存在しない

これは[ADR-0011](https://github.com/ch32-riscv-ug/ArduinoCore-CH32/blob/main/docs/adr/0011-tool-mirror-repository.ja.md)
の再配布理由**R-1 構造**にも**R-2 可用性**にも当たらない第3の理由であり、
`mirror-*`とは信頼モデルが違う。ミラーは「upstreamの成果物をバイト単位で転送し、
検証を上乗せしない」ものだが、**ここでは我々が製造者になる**。照合の対象は
upstreamのchecksumではなく**ビルド手順**になる。名前を`build-`にしているのはそのため。

## 2. スコープ

### 対象

- workflowが1回だけ解決したupstream commitからのhostごとのビルド
- libusbのstaticリンクによる自己完結化
- 単一rootディレクトリを持つアーカイブの生成
- Arduino tool定義fragment(`tools_minichlink.json`)の生成
- GitHub Releasesでの公開と、ビルド手順の記録

### 対象外

- **upstreamへのpatch。** sourceは無改造で使う。直したいことがあればupstreamへPRを出す
- minichlink自体の機能追加、bug修正、動作保証
- upstreamの検証。pinしたcommitを取得してコンパイルするだけで、汚染されていれば
  こちらも汚染される
- consumer側のversion採用判断
- `minichlink.so` / `minichlink.dll`(library形態)。要求が出るまで作らない

## 3. 成果物

`v<version>` tagのreleaseに次を添付する。

| 成果物 | 数 | 内容 |
|---|---:|---|
| hostごとのアーカイブ | 6 | 単一rootディレクトリ`minichlink-<version>/` |
| `tools_minichlink.json` | 1 | Arduino tool定義fragment |

repositoryにcommitするものは`versions/<version>.json`(§9)だけ。アーカイブはcommitしない。

### アーカイブの中身

```text
minichlink-<version>/
├── minichlink              (Windowsは minichlink.exe)
├── LICENSE                 upstream(ch32fun)のもの
├── COPYING                 libusbのもの
└── 99-minichlink.rules     Linuxのみ。upstreamのもの
```

形式はLinux/macOSが`.tar.gz`、Windowsが`.zip`。

`99-minichlink.rules`をLinuxに入れるのは、ArduinoCore-CH32側にudev rulesの配布と
案内が`[P1]`で残っているため。**installしただけでは適用されない**ので、案内は
consumer側の文書の役目とする。

## 4. version採番

minichlinkに自前のversionは無い。`VERSION`文字列はMakefileが計算する**自身のsourceの
SHA-1**で、実測では`bfff1cf2158794a1676d65d1ec2fc1d7d54f555b`(upstream `6c4dd53`時点)。
そこでこのrepositoryが採番する。

```text
YYYY.M.D-g<short-sha>-r<build-revision>
例: 2026.8.24-g6c4dd53-r1
```

- 日付は**upstream commitのcommitter date**(UTC)。**先頭0を付けない**(`8`であって`08`)
- 接尾辞はそのcommitの短縮SHA
- build revisionは`r1`から始め、同じupstream commitをbuild手順や依存の変更後に
  再buildするときは`r2`、`r3`と増やす
- upstream commitとbuild入力が同じものを2度公開しない
- Arduino公式indexに`1.8.0-48-gb176eee`のような`git describe`形式の前例があり、
  arduino-cliのversion比較(relaxed semver)は先頭0以外にはかなり寛容

同じ日でもcommitが異なればSHA部分が異なる。同じupstream commitでもbuild revisionが
異なれば別releaseになり、公開済みassetを差し替えずにbuild手順を修正できる。

## 5. ビルド定義

### 5.1 対象host

`arduino-cli`はentryの無いhostでは**toolだけでなくplatformのinstallごと失敗する**
(ADR-0011が実験で確認)。したがって6 hostすべてを埋める。空けてよいhostは無い。

| Arduino `host` | runner | コンパイラ | 状態 |
|---|---|---|---|
| `x86_64-pc-linux-gnu` | `ubuntu-latest` | `gcc`(native) | **手順を実測済み** |
| `aarch64-linux-gnu` | `ubuntu-24.04-arm` | `gcc`(native) | 未検証 |
| `x86_64-apple-darwin` | `macos-latest` | `cc -arch x86_64` | 未検証 |
| `arm64-apple-darwin` | `macos-latest` | `cc -arch arm64`(native) | 未検証 |
| `x86_64-mingw32` | `ubuntu-latest` | `x86_64-w64-mingw32-gcc` | 未検証 |
| `i686-mingw32` | `ubuntu-latest` | `i686-w64-mingw32-gcc` | 未検証 |

arduino-cliのhost照合は正規表現(`x86_64-.*linux-gnu`、`(aarch64|arm64)-linux-gnu`、
`x86_64-apple-darwin.*`、`arm64-apple-darwin.*`、`(amd64|x86_64)-.*(mingw32|cygwin)`、
`i[3456]86-.*(mingw32|cygwin)`)。上表の表記はいずれもこれに一致する。

### 5.2 libusb

**全hostでstaticリンクする。** 利用者にlibusbのinstallを要求しないため。

- upstreamの**releaseアーカイブ**を使う(`libusb-<ver>.tar.bz2`)。生成済みの`configure`が
  入っているため**autotoolsのinstallは不要**。upstreamのCIは`git clone` + `autogen.sh`の
  ために automake/autoconf/libtool を入れているが、こちらでは要らない
- 取得後、**checksumを検証してから展開する**。versionとchecksumはworkflowの`env`に
  固定し、`versions/<version>.json`に記録する
- 初版は`1.0.29`
  (SHA-256 `5977fc950f8d1395ccea9bd48c06b3f808fd3c2c961b44b0c2e6e29fc3a70a85`)

configureは最小構成にする。

```sh
./configure --disable-shared --enable-static --disable-udev \
            --disable-examples-build --disable-tests-build
```

`--disable-udev`でよいことは実測で確認済み。この設定でビルドしたlibusbは
`lsusb`と同じデバイスをすべて列挙する。minichlinkはhotplugを使わないため影響しない。

クロスビルドでは`--host=<triple>`を、macOSの非nativeアーキではあわせて
`CFLAGS`/`LDFLAGS`に`-arch <arch>`を渡す。

> **注意**: upstreamのCIはmacOSで2アーキのstatic libusbを`lipo`でuniversalに
> まとめている。こちらはhostごとに1アーキのアーカイブを出すので、その必要は無い。
> アーキごとに個別にビルドすればよい。

### 5.3 minichlink自身

- **`-ludev`は外せない。** libusb経由ではなく**minichlink自身が`pgm-esp32s2-ch32xx.c`で
  libudevを直接呼んでいる**(`udev_enumerate_*`、`udev_device_new_from_syspath`ほか)。
  外すにはupstreamへのpatchが要るので、[§2](#2-スコープ)により外さない。
  結果としてLinuxバイナリは`libudev.so.1`に動的依存する。systemdの一部であり、
  Arduino IDEが動く環境には必ずある。**落とせたのは`libusb-1.0.so.0`のほう**で、
  そちらは別パッケージのため入っているとは限らない
- **リリース用フラグを使う。** upstreamのMakefileは`-O0 -g3`かつstripしない。
  最適化してstripする(実測: unstripped 1,114,000 byte → stripped 320,560 byte)
- Linux/macOSは`make minichlink`に`CFLAGS`/`LDFLAGS`を渡して上書きする。
  コマンドラインの変数指定はMakefile内の`:=`より優先される
- **Windowsはmakeのターゲットを使えない。** `minichlink.exe`のrecipeが
  `x86_64-w64-mingw32-gcc`をハードコードしており、i686に振り替えられない。
  Makefileから`C_S`(sourceの一覧)を読み取り、コンパイラを直接起動する。
  sourceの一覧をこちら側に書き写さないこと。upstreamがファイルを増やしたときに壊れる
- Windowsのリンクは`-lsetupapi -lws2_32`に加え、static libusbが要求するWindows APIの
  ライブラリが要る(`-lcfgmgr32 -lole32 -ladvapi32`程度)。**実測で確定させること**

`minichlink`のビルドには`minichlink/`だけでなく**repository全体が要る**
(`minichlink.c`が`../ch32fun/ch32fun.h`をincludeしている)。

### 5.4 ビルドはスクリプトに寄せる

hostごとの分岐をworkflowのYAMLに書かず、`build.sh <host>` 1本に集約する。
理由は**手元で再現・検証できること**。CIでしか走らない手順は、壊れたときに
直すのが高くつく。workflowはcheckout、`build.sh`の呼び出し、artifactのupload
だけにする。

`build.sh`は`dist/<host>/`に次を出力する。

- アーカイブ1つ
- `build.json` — `emit_fragment.py`が読む(§9の`builds[]`の元データ)

## 6. 受け入れ検査

`build.sh`の中で、そのhostのバイナリが実行できる場合に必ず行う。
クロスビルドしたものは実行できないため、実行を伴う検査は省略し、
省略した事実をログに残す(黙って飛ばさない)。

| 検査 | 内容 |
|---|---|
| **`-l`の存在** | `minichlink -h`の出力に`-l `があること |
| help | `-h`がhelpを表示すること。終了値は記録する(upstreamは現在`255`) |
| 動的依存 | Linuxは`ldd`、macOSは`otool -L`。**`libusb`が現れないこと** |
| アーカイブ構造 | 展開してroot直下がディレクトリ1つだけであること |
| 同梱物 | バイナリ、`LICENSE`、`COPYING`、(Linux)`99-minichlink.rules`があること |

**`-l`の検査は必須。** 既存の配布物にはこれを持たないものがある。UIAPduinoコアが配る
`minichlink-2982dfd/1.0.0`は`-l`を`Error: Unknown command l`で拒否する古い世代で、
serial指定ができない。同じ轍を踏まないための検査であり、外さないこと。

Windows実行形式の検査手段(`objdump -p`によるimport確認など)は実装時に決める。

### 実機動作

実機での書き込み、terminal、GDB serverの検査はこのrepositoryの受け入れ条件に含めない。
成果物はbuild済みbinaryとして提供するだけで、特定のprobe、target、OSでの動作を保証しない。
利用者が自分の要件に応じて評価し、採用を判断する。

## 7. Workflow

### 7.1 `build.yml` — 公開する

- `schedule`でupstreamの既定branchを確認し、最新commitが未releaseならbuildとreleaseを
  自動実行する。既にrelease済みのcommitなら何もしない
- `workflow_dispatch`でも起動できる。入力は`ref`(upstreamのcommit-ish、既定`master`)と
  `dry_run`(booleanで、releaseを作らずartifactだけ出す)
- **commitは最初に1回だけ解決する。** 解決した完全SHAを全matrix legへ渡す。
  legごとに`master`をcheckoutすると、途中でpushされたときにhostごとに違うsourceから
  ビルドされる
- `concurrency`で同時実行を禁止する
- **append-only。** `v<version>`が既にあれば、ビルドを始める前に失敗させる。
  既存tagへの再uploadと、既存`versions/<version>.json`の上書きを禁止する
  (`emit_fragment.py`は上書きを拒否して終了する)
- `fail-fast: false`。1 hostの失敗で他のhostの情報を失わない。ただし**6 host揃わなければ
  publishしない**(`emit_fragment.py`が欠けを検出して失敗する)
- release notesに、成果物はbuild outputであり実機動作を保証しないことを明記する

### 7.2 upstream更新の取扱い

更新確認とbuildを別workflowに分ける場合、`watch.yml`は未releaseのupstream commitを
見つけたときに`build.yml`を起動する。1回の確認で取得した完全SHAをそのまま渡し、後から
動いたbranch名をbuild側で再解決しない。

upstreamの各commitを必ずreleaseする必要はない。確認時点の最新commitが未releaseなら
そのcommitをreleaseすればよく、確認間隔の間に通過したcommitは飛ばしてよい。
scheduleの自動停止対策はworkflow実装時に入れる。

### 7.3 責務の境界

GitHub Releaseはbuild可能性と配布物の構造・metadataが自動検査を通過したことだけを示す。
実機動作、consumerの要件への適合、versionの採用は保証しない。

```text
upstreamまたはbuild手順の変更
    → GitHub Actionsでbuild・自動検査
    → GitHub Releaseを公開
```

利用者側の実機テスト、PIN、採用手順はこのrepositoryでは管理しない。build手順または依存を
修正して同じupstream commitを再buildする場合は、build revisionを増やして新しいreleaseを
作る。古いreleaseとassetは残し、同じversionを修正しない。

## 8. 配布物の消さない運用

- 古いversionのreleaseとassetを**消さない**。package indexはappend-onlyで、
  古いplatform versionがpinしているtoolを消すと**過去のplatformがinstallできなくなる**
- 公開済みtagを別commitへ付け替えない
- 公開済みassetを差し替えない。差し替えたいときは新しいversionを出す

## 9. `versions/<version>.json`

ここが**照合の根拠**になる。ミラーと違ってupstreamのchecksumが存在しないため、
第三者が再現できるだけの情報を残すことが、この文書全体でいちばん重要な要件である。

記録するもの:

| 項目 | 内容 |
|---|---|
| `version` / `name` | 採番したversion、`minichlink` |
| `upstreamRepository` / `upstreamCommit` / `upstreamCommittedAt` | 完全SHAとcommit日時 |
| `builderCommit` / `buildRevision` | このrepositoryのbuild定義を含むcommit、`r1`から始まるrevision |
| `libusb` | version、URL、SHA-256、`linkage: static` |
| `systems[]` | hostごとのURL、ファイル名、SHA-256、size(=fragmentと同じ) |
| `builds[]` | hostごとのrunner、コンパイラとその`--version`、`cflags`、`ldflags`、動的依存の一覧 |

`emit_fragment.py`が生成する。**実装済み。**

## 10. ライセンス要件

| 対象 | ライセンス | 義務 |
|---|---|---|
| このrepository自身のファイル | MIT(rootの`LICENSE`) | — |
| minichlink(ch32fun) | MIT | `LICENSE`をアーカイブに同梱 |
| libusb | **LGPL-2.1-or-later** | 下記 |

libusbを**staticリンク**するため、LGPL-2.1 §6が定める条件を満たす必要がある。
受領者が改変したlibusbで再linkできるようにすることに加え、配布方法に応じたsourceまたは
object code等の提供条件を、初release前に確認する。`versions/<version>.json`へlibusbの
正確なversionとchecksum、minichlinkのcommit、hostごとのcompilerとflagsを記録することは
再現と再linkを助けるが、**metadataだけでlicense条件を満たすとは扱わない**。

`COPYING`(libusb)をアーカイブに同梱すること。詳細は
[`THIRD-PARTY-NOTICE.md`](../THIRD-PARTY-NOTICE.md)。

## 11. 実装時の確認事項

方針は決定しているが、実装または運用開始までに確認が必要な事項を示す。

| # | 事項 | 決定した方針 | 残る確認 |
|---|---|---|---|
| C-1 | `i686-mingw32` | 32 bit binaryを実ビルドする | static libusbを含むlinkとimport DLLを実測する |
| C-2 | libusbのlink方式 | 全hostでstatic linkする | macOS、Windows、Linux Arm64でbuildと依存を実測する |
| C-3 | Windows link library | mingw-w64で直接compilerを起動する | x86-64、i686それぞれの必要libraryを確定する |
| C-4 | ArduinoCore-CH32のADR | ADR-0011へ`R-3`と`build-`接頭辞を追記する | consumer repository側で別途変更する |
| C-5 | LGPL-2.1 §6への対応 | static linkを維持し、再link可能な資料を提供する | 初releaseの配布物とsource／object codeの提供方法を確認する |
| C-8 | upstream確認間隔 | scheduleで自動確認する | 日次などの実行間隔を決める |
| C-9 | version記録のcommit方法 | `versions/<version>.json`をrepositoryへ残す | Actionsからdefault branchへ直接commitする権限と、tag・release作成順を決める |
| C-10 | libusbの更新 | minichlinkとは独立してversionとchecksumを固定する | 自動追従せず手動更新とするか決める |

## 12. 調査結果

この文書の数値と挙動について、確認済みのものと未確認のものを分ける。確認時期は
repositoryの履歴で確認する。

### 確認済み(Linux x86_64)

| 内容 | 値・結果 |
|---|---|
| upstream releaseの有無 | GitHub API。host別のminichlink binary assetは無い |
| libusb tarballのchecksum | `5977fc950f8d1395ccea9bd48c06b3f808fd3c2c961b44b0c2e6e29fc3a70a85` |
| autotools不要 | autoconf/automake/libtoolが**未installの環境**で`./configure`が通り、`libusb-1.0.a`(920,244 byte)ができた |
| `--disable-udev`でも列挙できる | そのstatic libusbで書いた列挙プログラムが9デバイスを返し、`lsusb`と一致 |
| minichlinkがlibudevを直接使う | `-ludev`無しでリンクすると`pgm-esp32s2-ch32xx.c`の`udev_*`が未解決になる |
| ビルドの成立 | `make minichlink LDFLAGS="-lpthread <libusb-1.0.a> -ludev"` が通る |
| 動的依存 | `ldd` → `libudev.so.1`、`libc.so.6`、`libcap.so.2`。**`libusb-1.0.so.0`は消えた** |
| サイズ | unstripped 1,114,000 byte / stripped 320,560 byte |
| `-l`の存在 | `-l [programmer USB serial; omit for default device selection]` |
| minichlinkの`VERSION` | `bfff1cf2158794a1676d65d1ec2fc1d7d54f555b`(sourceのSHA-1) |
| Makefileの制約 | `minichlink.exe`のrecipeが`x86_64-w64-mingw32-gcc`をハードコード。`minichlink`のrecipeは`gcc`をハードコード |
| ビルドにrepository全体が要る | `minichlink/`だけをコピーすると`../ch32fun/ch32fun.h`が見つからない |
| arduino-cliのhost照合 | arduino-cliバイナリ内の正規表現(`x86_64-.*linux-gnu`ほか)を確認 |
| tool versionの前例 | 手元のpackage index 214種のうち`1.22.0-80-g6c4433a-5.2.0`、`1.8.0-48-gb176eee`などが実在。先頭0を持つ数値フィールドは1件も無い |

### 未確認

- **macOS 2種、Windows 2種、aarch64のビルド**。上流CIにmacOSとWindows(x86_64)の
  前例はあるが、こちらの構成(static libusb、リリースフラグ、i686)では未検証
- Windowsのstatic libusbが要求するライブラリの正確な一覧
- **実機での書き込み・デバッグ動作**。このrepositoryの保証・受け入れ検査の対象外
- `ubuntu-24.04-arm` runnerでのビルド

## 13. 参照

- [ADR-0011: 再配布が必要なtoolは1ツール1repositoryでミラーする](https://github.com/ch32-riscv-ug/ArduinoCore-CH32/blob/main/docs/adr/0011-tool-mirror-repository.ja.md)
- [mirror-probe-rs](https://github.com/ch32-riscv-ug/mirror-probe-rs) — 様式の元
- [ch32fun](https://github.com/cnlohr/ch32fun) / [upstreamのCI](https://github.com/cnlohr/ch32fun/blob/master/.github/workflows/minichlink.yml)
- [Arduino package index specification](https://arduino.github.io/arduino-cli/latest/package_index_json-specification/)
