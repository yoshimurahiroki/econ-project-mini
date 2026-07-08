

# econ-project

Python，R，TinyTeX，Quarto，Jupyter Notebook，クラウドIDEエージェント向けの経済学研究ワークスペースです。Dev Container を起動すれば研究用インフラが揃う一方で，AI コンテキストとコンテナサイズを小さく保つ設計にしています。

分析用パッケージは，デフォルトでは最小限しか入れません。研究や再現作業で必要になった時点で，Python は `pixi` または `uv`，R は `rv` で明示的に追加します。

## 環境

リポジトリを Dev Container で開いてください。コンテナには次の基盤を用意します。

* Python 実行環境は `pixi` で管理
* R パッケージは `rv` と `rproject.toml` で管理
* LaTeX は軽量な TinyTeX を使用
* Quarto と Pandoc による HTML / PDF 生成
* Jupyter Notebook / JupyterLab と Python・R カーネル登録
* 対応IDE向けのコンパクトな AI ルールと MCP 設定
* `ripgrep` による軽量なファイル検索

## 依存関係の同期

コンテナ作成時に環境は自動同期されます。手動で同期する場合は次を使います。

```bash
make sync
make r-install
```

Python コマンドは，原則として `pixi run` 経由で実行します。

```bash
pixi run python scripts/sync_rules.py
```

## Python パッケージの追加

このプロジェクトでは，Python 実行環境の基本管理には `pixi` を使います。`conda-forge` にあるパッケージは `pixi add` で追加します。

```bash
# 例: conda-forge から Python パッケージを追加
pixi add numpy

# 複数パッケージをまとめて追加
pixi add pandas pyarrow

# 環境を同期
pixi install

# 追加後の確認
pixi run python -c "import numpy; print(numpy.__version__)"
```

`conda-forge` にない PyPI パッケージ，または PyPI 版を明示したいパッケージは，同じ `pixi` 環境に PyPI 依存として追加します。

```bash
pixi add --pypi some-package
pixi run python -c "import some_package"
```

`uv` は，Python プロジェクト依存を `pyproject.toml` / `uv.lock` で管理したい場合に使います。`uv` を使う場合は，`.pixi` 環境とは別に `.venv` が作られることがあります。同じパッケージを `pixi` と `uv` の両方で二重管理しないでください。

```bash
# uv が未導入なら，まず pixi 環境に追加
pixi add uv

# pyproject.toml に依存を追加し，uv.lock と .venv を更新
uv add requests

# uv 管理環境で実行
uv run python -c "import requests; print(requests.__version__)"

# 依存を削除
uv remove requests

# 特定パッケージだけ更新
uv lock --upgrade-package requests
```

使い分けの目安は次の通りです。

* Dev Container 全体の実行基盤や Jupyter から使う分析環境に入れたい場合: `pixi add`
* PyPI にしかないが，`.pixi` 環境内で使いたい場合: `pixi add --pypi`
* Python パッケージとして配布・ロック・実行を `uv` に寄せたい場合: `uv add` / `uv run`

## R パッケージの追加

R パッケージは `rv` で管理します。通常は `rv add` で `rproject.toml` に依存を追加し，そのまま同期します。

```bash
# 例: CRAN パッケージを追加して同期
rv add fixest

# 複数パッケージを追加
rv add dplyr ggplot2

# 追加だけ行い，同期は後で実行
rv add --no-sync modelsummary

# 手動同期
make r-install
# または
rv sync
```

GitHub などの Git リポジトリから追加する場合は，`--git` を使います。

```bash
rv add mypackage --git https://github.com/user/mypackage.git
```

R セッション内で `install.packages()` を直接使うと，`rproject.toml` と `rv.lock` に反映されないことがあります。再現性を保つため，原則として `rv add` または `rproject.toml` の編集後に `rv sync` を使ってください。

## AI Surface

`.cursorrules` が単一の正式ポリシーです。ほかの IDE ファイルは，コンパクトな参照ポインタまたは生成された MCP 設定として扱います。

プロジェクトスキルは `.agents/skills` に置きます。ここには軽量な入口ファイルだけを置きます。外部スキル repo の clone は任意です。通常のセットアップでは `.resources` は不要です。

`.resources` を使う場合でも，AI に repo 全体を読ませてはいけません。`rg` や `rg --files` で必要なファイルを探し，該当する小さいファイルまたは必要な抜粋だけを読みます。

現在のスキル入口:

* `academic-research-resources`
* `causal-inference-resources`
* `ecc-resources`
* `econ-ai-resources`
* `econ-research-feedback`
* `econ-writing`

任意の外部スキル repo clone を取得する場合は次を実行します。

```bash
make ai-references
```

取得される場所:

* `.resources/econ-ai/AI-research-feedback`
* `.resources/econ-ai/awesome-ai-for-economists`
* `.resources/econ-ai/awesome-causal-inference`
* `.resources/econ-ai/awesome-econ-ai-stuff`
* `.resources/econ-ai/econ-writing-skill`
* `.resources/research-ai/ECC`
* `.resources/research-ai/academic-research-skills`

通常の `make test` は `.resources` がなくても通ります。外部スキル repo まで取得・検証したい場合だけ `make ai-references` を使います。

## トークン消費を抑える運用

基本方針は次の通りです。

* 起動時に外部 repo，README，docs 全体を読ませない
* 常時使うのは `.agents/skills` の短い入口ファイルだけにする
* `.resources` は任意で，必要なときだけ取得する
* `.resources` を使う場合は，まず `rg` / `rg --files` で探す
* 開くのは最小の該当ファイルまたは抜粋だけにする
* `docs/ai/compiled_ai_skills.md` は索引として扱い，起動時コンテキストには入れない
* `token-optimizer` や `codebase-memory` 系 MCP は，必要な場面でだけ有効にする

MCP の context 補助ツールを有効にする場合は，明示的に次を使います。

```bash
ENABLE_CONTEXT_MCP=1 bash scripts/setup_ide_mcp.sh
```

デフォルトでは有効にしません。通常は `rg` による検索と短いスキル入口で十分です。

## コマンド

```bash
make test          # agent / MCP / rule のスモーク検証
                   # tests が存在する場合は pytest も実行
make ai-references # 任意の外部スキル repo を取得して検証
make check         # ruff，format check，mypy，tests / smoke validation
make format        # ruff format と autofix
make r-install     # rv で R 依存関係を同期
```

LaTeX と Quarto:

```bash
make build-paper
make build-slides
make quarto-html
make quarto-pdf
```

## クリーンアップ

生成キャッシュやレポートはソースとして管理しません。

* `.agent_state`
* `.pytest_cache`, `.mypy_cache`, `.ruff_cache`
* `__pycache__`
* `.coverage`
* TeX と Quarto のビルド成果物

削除する場合は次を実行します。

```bash
make clean
```
