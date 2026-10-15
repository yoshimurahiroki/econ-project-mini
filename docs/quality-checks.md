# 変更したコードの検査

AI がコードを作成・変更したら、完了報告前に `git status --short` と差分から新規・変更ファイルを確認し、下表の検査と影響する小さなテストを実行する。指摘の原因を読み、妥当な欠陥を修正して再検査する。研究上の標本選択・処置分類・推定方法は検査の都合で変更しない。実行コマンド、結果、未検証の理由を報告する。人が checker を選び直すことを前提にしない。

## 入口と発火条件

| 対象の変更 | 検出すること・実行入口 | commit / CI |
| --- | --- | --- |
| Python `.py` | `make quality FILE=path.py`：Ruff の構文エラー、未定義名、壊れた比較・例外処理など（`E9,F63,F7,F82`）。通常の `make lint FILE=path.py` は未使用 import 等も確認 | staged / PR 差分の Python に必須検査 |
| `scripts/build_latex.py` | 同じ `quality` 入口で mypy。既存の `Path` 入力と戻り値の契約を確認 | このファイルに必須検査 |
| 他の Python の入出力境界・再利用関数 | 変更した関数の入力・戻り値に必要な注釈を付け、`make typecheck FILE=path.py`。実データ依存を増やさず検証できた境界は hook の `mypy-boundaries.files` に加える | 採用した境界だけ段階的に必須化 |
| shell（`.sh` / shell shebang） | `make quality FILE=path.sh`：ShellCheck の未定義変数、壊れた条件式等。warning 以上を必須扱い。`pixi run -e quality shellcheck --severity=info path.sh` で未引用展開等の参考診断も読む | staged / PR 差分の shell に必須検査 |
| `.Rprofile` | `make r-parse FILE=.Rprofile`：実行せず構文解析。起動時のパス探索・library 変更は小さな fixture でも確認 | AI が変更時に実行。軽量 CI には R を導入しない |
| Python の整形 | 必要時に `make format-check FILE=path.py` で差分の有無を確認 | 参考。既存書式の一括変更を要求しない |
| 単位、キー、結合多重度、欠損とゼロ、標本、分母 | 変更した処理の既存テスト・小さな入力・データ条件の assertion で確認 | 型や lint の成功では代替できない |

`make quality FILE=path` は作業中・新規ファイルを一つ指定できる。複数なら `pixi run -e quality pre-commit run --files path1 path2`。`make quality-staged` は staged ファイル、`make quality-changed BASE=ref` はその ref と HEAD の間の **commit 済み差分だけ** を検査する。未 commit・未追跡ファイルには `FILE` / `--files` を使う。pre-commit がファイル種別から checker を選ぶため、無関係な全ツリーを検査しない。

hook の非ゼロ終了は必須失敗。ツール未導入も成功扱いにしない。通常 lint の未使用 import 等、ShellCheck info、formatter の差分は確認材料であり、内容を読んで必要性を判断する。例えば shell 内の sed 式にある literal `$PATH` は SC2016 が出ても意図通りであり、自動で引用を変えない。必須規則の除外や `type: ignore` で同じ診断をまとめて隠さない。正当な例外が必要なら、その行・理由・動作を確かめるテストを示す。mypy は全ファイル strict にせず、推移 import の一括無視もしない。

修正は別操作である。Ruff / ShellCheck / mypy の hook は書き換えない。整形が必要なファイルだけ `make format FILE=path.py` を実行して差分を読む。lint の `--fix`、特に unsafe fix を自動で適用しない。IDE の保存時 lint・型検査・自動修正は従来どおり無効。EditorConfig は入力時の改行・字下げ規約を供給する。

## 小さなテスト

`make test TEST=path::node` は既存の研究環境で対象テストを実行する。文書ビルド入口を変更した場合、外部 TeX を使わない失敗・PDF 復元・空白を含むパスの回帰確認は次のコマンドで行える。

```sh
pixi run -e quality pytest -q -p no:cacheprovider scripts/test_build_latex.py::BuildTests
```

MCP 設定生成を変更した場合は `scripts/test_setup_ide_mcp.py`、共通ファイル同期を変更した場合は `scripts/test_sync_common_core.py` を指定する。CI も該当ファイルの変更時だけこれらの小さなテストを実行する。実 LuaLaTeX / Quarto の検証は文書変更に応じて既存環境で別途実行し、skip は未検証として報告する。重い分析を品質検査のために起動しない。

## 導入条件と版

Python と shell はこの repo で実際に使うため、既存の `pyproject.toml` に専用の Pixi `quality` environment を定義した。`no-default-feature = true` で研究・文書環境の **インストール** を避ける。依存解決は Pixi が同じ manifest 全体を扱う。mini はもともと lock を追跡していないため、直接の checker 版を固定し、生成された lock はこの変更で配布しない。

```sh
make setup-quality  # pixi install -e quality と pre-commit install
make quality FILE=scripts/build_latex.py
```

`pixi` 自体が利用可能なら checker がない場合もこの正規経路で導入できる。`pixi run -e quality ...` も必要な環境を準備する。コード変更がなく文書だけなら checker の追加導入は不要。CI は PR の HEAD を checkout し、同じ pre-commit 設定で merge-base からの変更だけ検査する。private key 検出も維持する。

| 道具 | 採用版・公式資料 | 判断 |
| --- | --- | --- |
| Ruff | 0.16.9、[linter](https://docs.astral.sh/ruff/linter/)、[release](https://github.com/astral-sh/ruff/releases/tag/0.16.9) | 既存利用を継続。必須規則を限定し、整形を分離 |
| mypy | 2.3.1、[既存コードへの適用](https://mypy.readthedocs.io/en/stable/existing_code.html)、[release](https://github.com/python/mypy/releases/tag/v2.3.1) | 既に注釈がある境界から開始。型だけで入力値の妥当性は保証しない |
| pre-commit | 4.3.0、[run / files / refs](https://pre-commit.com/#pre-commit-run) | 既存入口で変更ファイルを選択。別の汎用検査 framework は作らない |
| ShellCheck | 0.11.0、[release](https://github.com/koalaman/shellcheck/releases/tag/v0.11.0)、[使い方](https://github.com/koalaman/shellcheck#how-to-use) | 実際に使う shell の warning 以上。shfmt は整形需要がないため見送り |
| pytest | 9.1.1、[選択実行](https://docs.pytest.org/en/stable/how-to/usage.html#specifying-which-tests-to-run) | 既存の小さなテストを指定実行 |
| Pixi | CI / 検証 0.82.0、[複数環境](https://pixi.prefix.dev/latest/workspace/multi-environments/)、[setup-pixi](https://github.com/prefix-dev/setup-pixi/tree/v0.11.1) | 既存依存管理で checker を隔離 |

mini には研究用 R source、手書き JS / TS、Julia、単独 SQL がまだない。R を追加・変更するときはまず `pixi run Rscript --vanilla -e 'for (p in c("lintr", "styler")) print(c(p, if (requireNamespace(p, quietly=TRUE)) as.character(packageVersion(p)) else "missing"))'` と通常の project 起動環境の両方で導入状況を調べる（rv の library が `.Rprofile` から追加される）。必要な lintr は `rv add lintr` / `make r-install`、整形需要がある場合だけ styler を同じ経路で追加する。既に利用できる推移依存を未導入とみなさず、hook / CI に採用するなら直接依存として版と限定規則を管理し、実コードでノイズを確かめる。構文確認だけなら新しい R package は不要。

Biome は手書き JS の採用時、TypeScript compiler は TS の採用時、Runic / JET は Julia の採用時に検討する。SQLFluff は実在する SQL と方言に対して費用に見合う場合だけ。導入のための埋込み SQL 抽出基盤は作らない。
