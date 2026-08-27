# Third-party content

The root [`LICENSE`](LICENSE) (MIT) covers **only this repository's own files** —
the planned workflows, `emit_fragment.py`, and the documentation. It does
**not** replace the terms that apply to third-party content in release assets.

## minichlink (ch32fun)

The binaries planned for this repository's releases are builds of
[minichlink](https://github.com/cnlohr/ch32fun/tree/master/minichlink), part of
[ch32fun](https://github.com/cnlohr/ch32fun):

- **Copyright** CNLohr and the ch32fun contributors
- **License** MIT
- Upstream's `LICENSE` is inside every archive
- Upstream's `99-minichlink.rules` is inside the Linux archives

## libusb

The initial design statically links [libusb](https://github.com/libusb/libusb)
into every binary:

- **Copyright** the libusb contributors
- **License** LGPL-2.1-or-later
- Upstream's `COPYING` is inside every archive

[LGPL-2.1 §6](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html#SEC6)
places conditions on distribution of an executable statically linked with the
library, including enabling recipients to relink it with a modified library.
The exact obligations depend on the distribution method and are not replaced
by build metadata alone.

Before the first release, the project must verify that the release provides or
validly offers all material required by the license. The planned build record
— exact libusb version and checksum, minichlink commit, compiler, and flags —
supports reproducibility and relinking, but this pre-implementation repository
does not yet claim that a compliant release bundle exists.

## What the build changes

**No source file is modified.** No patch is applied to ch32fun or to libusb.
The upstream commit is pinned per release and recorded, so the input can be
checked out and inspected.

What differs from typing `make` in `minichlink/` is the build environment only:

- **libusb is linked statically**, from an upstream release tarball, so users do
  not have to install it. Upstream's own Makefile links it dynamically on Linux
  and Windows (its CI ships `libusb-1.0.dll` beside `minichlink.exe`), and
  statically on macOS.
- **Release flags** replace upstream's `-O0 -g3`: optimised and stripped.
- **The archive** places the binary under a single root directory, which is what
  `arduino-cli` requires.

`libudev.so.1` remains a dynamic dependency on Linux, because minichlink calls
libudev directly in its ESP32-S2 programmer backend. Removing it would require
patching upstream, which this repository does not do.

## This is not an endorsement

These builds are intended to be produced by the CH32 RISC-V User Group and are **not affiliated
with, endorsed by, or supported by ch32fun, CNLohr, or the libusb project**.
Report problems with minichlink itself to ch32fun; report problems with these
builds or their packaging here.

---

## 日本語

ルートの[`LICENSE`](LICENSE)(MIT)は**このrepository自身のファイル**
(予定しているworkflow、`emit_fragment.py`、文書)にのみ適用されます。release assetに
含まれる第三者著作物の条件を置き換えるものではありません。

### minichlink(ch32fun)

releaseで配布する予定のバイナリは
[minichlink](https://github.com/cnlohr/ch32fun/tree/master/minichlink)であり、
[ch32fun](https://github.com/cnlohr/ch32fun)の一部です。

- **著作権** CNLohr および ch32fun contributors
- **ライセンス** MIT
- upstreamの`LICENSE`を各アーカイブに同梱しています
- upstreamの`99-minichlink.rules`をLinux向けアーカイブに同梱しています

### libusb

初版設計では、すべてのバイナリに[libusb](https://github.com/libusb/libusb)を
static linkします。

- **著作権** libusb contributors
- **ライセンス** LGPL-2.1-or-later
- upstreamの`COPYING`を各アーカイブに同梱しています

[LGPL-2.1 §6](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html#SEC6)は、
libraryをstatic linkした実行ファイルの配布に、受領者が改変したlibraryで再linkできる
ようにすることを含む条件を定めています。具体的な義務は配布方法によって変わり、build
metadataだけで置き換えられるものではありません。

初releaseの前に、licenseが要求する資料の同梱または有効な提供方法を確認します。libusbの
正確なversionとchecksum、minichlinkのcommit、hostごとのcompilerとflagsを記録する設計は
再現と再linkを助けますが、実装前の現時点では「releaseが条件を満たす」とは表明しません。

### ビルドが変えているもの

**sourceは一切変更していません。** ch32funにもlibusbにもpatchを当てていません。
upstream commitはreleaseごとにpinして記録してあるため、入力をcheckoutして
確認できます。

`minichlink/`で`make`するのとの違いは、ビルド環境だけです。

- **libusbをstaticリンク**します(upstreamのreleaseアーカイブから)。利用者が
  libusbを入れる必要をなくすためです。upstreamのMakefileはLinuxとWindowsでは
  動的リンクで(CIは`libusb-1.0.dll`を`minichlink.exe`と一緒に配っています)、
  macOSではstaticです
- **リリース用フラグ**を使います。upstreamの`-O0 -g3`ではなく、最適化してstripします
- **アーカイブ**は`arduino-cli`の要求どおり、バイナリを単一のrootディレクトリの下に
  置きます

Linuxでは`libudev.so.1`が動的依存として残ります。minichlinkがESP32-S2向け
programmerで**libudevを直接呼んでいる**ためで、外すにはupstreamへのpatchが要ります。
このrepositoryはpatchを当てません。

### 推奨ではありません

これらのビルドはCH32 RISC-V User Groupが作成する予定で、**ch32fun、CNLohr、
libusbプロジェクトとは無関係**です。推奨・支援を受けているものでもありません。
minichlink自体の問題はch32funへ、ビルドや梱包の問題はこちらへ報告してください。
