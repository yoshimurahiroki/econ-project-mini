# econ-project-mini

Economics Research Skills（ERS）の研究スキル、経済学知識、実行・成果物管理を保守する正本。研究質問と識別条件の整理から、データ取得、推定・均衡計算、図表、論文・スライドまでを、同じ採用仕様と保存結果から一貫して作成する。

Python・R・Jupyter・Quarto・TinyTeXの基盤を備え、分析パッケージは研究ごとに選ぶ。広いPython・R分析環境とlockファイルをまとめて使う場合は、[econ-project](https://github.com/yoshimurahiroki/econ-project)を選ぶ。

## 使い始める

```sh
git clone https://github.com/yoshimurahiroki/econ-project-mini.git
cd econ-project-mini
```

コーディングエージェントの作業場所をこのフォルダーにし、[AGENTS.md](AGENTS.md)を入口にする。依頼には、研究上の問い、対象データ・資料、欲しい成果物、変更する範囲を添える。操作が決まっている場合はその担当Skillとモードへ進み、担当を探す場合は[操作一覧](docs/ai/compiled_ai_skills.md)を使う。必要な本文の取得と実行・完了の共通規則は[CORE](runtime/CORE.md)、表現は[PROSE](runtime/PROSE.md)にある。

| Skill | 担当する作業 |
| --- | --- |
| [econ-design](skills/econ-design/SKILL.md) | 研究質問、モデル、識別・推論設計、方法選択 |
| [econ-literature](skills/econ-literature/SKILL.md) | 文献調査、原文・引用・制度の確認 |
| [econ-data](skills/econ-data/SKILL.md) | データ取得・加工、推定・計算、研究コード、企業価値評価 |
| [econ-writing](skills/econ-writing/SKILL.md) | 執筆、改稿、翻訳、説明、論文・スライドへの変換 |
| [econ-review](skills/econ-review/SKILL.md) | 主張・計算・成果物の評価と指定範囲の修正 |
| [econ-knowledge](skills/econ-knowledge/SKILL.md) | 主担当が必要とする理論・モデル・判断条件の参照 |
| [project-work](skills/project-work/SKILL.md) | 要件・作業方針、実行プロンプト、案件への参加・運営 |

## 計算・文書作成の環境

DockerとVS CodeのDev Containers拡張を用意し、このフォルダーを「Reopen in Container」で開く。[コンテナ設定](.devcontainer/devcontainer.json)が[初期セットアップ](.devcontainer/setup-environment.sh)を実行し、Pixi環境とPython・RのJupyterカーネルを登録する。対象プラットフォームは`linux-64`、Rは4.5系。初回はネットワークから環境を取得する。

以降のコマンドはリポジトリのルートで実行する。

```sh
make help
pixi run python --version
pixi run R --version
```

基盤の依存定義は[pyproject.toml](pyproject.toml)にあり、R・IRkernel・Quarto関連の基盤パッケージもPixiが管理する。[rproject.toml](rproject.toml)には採用した研究のRパッケージを追加する。初期状態の依存リストは空である。変更後は次の入口で更新する。

```sh
make sync
make r-install
make register-kernels
```

miniの基盤はPython 3.12.13、R 4.5.3、Quarto 1.9.38、Pandoc 3.8.3に固定する。[econ-project](https://github.com/yoshimurahiroki/econ-project)のfullプロファイルが研究用依存、`pixi.lock`、`rv.lock`とJulia環境を管理する。各研究では採用した環境のlockと入力を保存する。初期セットアップのRパッケージ導入は`INSTALL_R_PACKAGES=1`で選べる。コンテナ内の作業場所は`/workspaces/<フォルダー名>`で、`data/`と`.pixi/`はDocker volumeに置く。Notebookでは`Python (フォルダー名)`または`R (フォルダー名)`を選ぶ。カーネルIDは作業場所ごとに保持する。

## 必要な経済学知識を選ぶ

[知識ライブラリ](skills/econ-knowledge/references/domains.json)は35章・256ユニット・34モデル契約を持つ。定義・数式・成立条件、観測と識別、最適行動・均衡・厚生、実装への対応を既存IDで参照できる。日英の概念・同義語とJEL分類で候補を探し、選んだIDと必要な前提だけを読む。

```sh
python3 skills/econ-knowledge/scripts/knowledge.py domains
python3 skills/econ-knowledge/scripts/knowledge.py search --query "広告 継続率 在庫" --limit 6
python3 skills/econ-knowledge/scripts/knowledge.py plan INNOV-04 --read
```

`relations`は知識間の関係と適用条件、`plan`は必要な本文とモデル契約を示す。ベイズ推定では事前・事後予測、階層モデル、計算診断、モデル比較から期待利益・損失による行動選択へ進む。ビジネス判断では広告・顧客維持、価格・商品・プラットフォーム、需要予測・在庫・容量、投資・信用・不動産・電力を扱う。具体的な入力・数式・選択条件は各ユニットに置く。

## 手法を選び、採用した研究を実行する

[研究実行ガイド](harness/research.md)に沿って、問い、推定対象、識別、標本、単位、期間、数値条件を仕様にする。PyBLPの需要・価格均衡、因果推論、動学モデル、ベイズ推定は、対応する公式パッケージと既存の実行入口へ接続する。MMM・CLV、階層需要予測、業務最適化などには17の任意選択プロファイルがあり、必要な依存だけを導入する。

選択仕様を`selection.json`に保存した場合は、次のコマンドで実装・導入条件・結果契約を取得する。

```sh
python3 skills/econ-design/scripts/research_design.py select selection.json \
  --root . --output outputs/selection.json
```

[公式実装の選択表](skills/econ-data/references/implementation-engines.md)で対象モデルを選び、[project-scriptの手順](skills/econ-data/references/implementation-calls.md#official-project-scripts)に従って`options.stage`へ研究プログラム、入力、出力、実行環境を渡す。選択結果の`install_requirements`またはR・Juliaの導入条件を使い、各手法の環境を復元する。主体間の取引・普及を計算する研究も、経済的な行動規則を指定したプログラムからMesa・NetworkXを利用する。

研究の段階と依存関係を記すmanifest（JSON）を`research.json`に保存したら、既存ランナーで実行する。

```sh
python3 harness/research.py --root . research.json
```

データ、仕様、コード、環境と上流結果が一致する完了済み段階は再利用する。入力の変更は依存する段階へ伝え、各計算で識別・推論・元の方程式・ソルバーの条件を確認する。実行状況と保存先はランナーの返り値と[状態管理](harness/state.md)に残る。

## 保存結果から成果物を作る

[結果の登録と図表・本文](skills/econ-writing/references/result-artifacts.md)では、推定結果の数量に単位、定義、生成元を対応させる。同じ保存結果から表・図・Quarto・LaTeX・HTML・PDFを作り、[結果ギャラリー](harness/research_gallery.py)で表示を編集する。自分の研究で登録したギャラリーを指定して開く。

```sh
pixi run research-ui -- --root . --registry path/to/research/gallery.json
```

[会議資料](harness/meetings.md)は保存図表と決定・作業記録を使い、[再現パッケージ](harness/research.md#package-and-reproduce-a-completed-research-result)は選択したデータ、コード、環境と完成結果をまとめる。表示だけの変更は対応する保存結果を使う。

[LaTeX論文](tex/paper/ecta_template.tex)、[Beamerスライド](tex/slides/main.tex)、Quartoの[論文](tex/paper/quarto_template.qmd)・[スライド](tex/slides/quarto_template.qmd)を編集してビルドできる。

```sh
make build-paper
make build-slides
make qmd-pdf QMD=tex/paper/quarto_template.qmd
make slides-pdf QMD=tex/slides/quarto_template.qmd
```

別のLaTeX原稿は`PAPER=...`、`SLIDES=...`で指定する。出力は原稿と同じディレクトリに置く。文書の書式と実行入口は[Makefile](Makefile)と[文書設定](docs/ai/integration.md#supplied-document-defaults)にある。

## 自分のプロジェクトと設定へ配置する

別のプロジェクトへ渡す指示は、担当操作とモードを選んで書き出す。出力先には新しいディレクトリを指定する。

```sh
python3 scripts/export_project.py --task econ-writing --mode compose \
  --output /tmp/ers-writing-mini-new
```

生成した`PROJECT_INSTRUCTIONS.txt`と参照ファイルをProjectに配置する。コーディングエージェント用の配置は`--format deployed`、プラグイン配布は[統合・配布手順](docs/ai/plugin-integration.md)を使う。文体の選択は[repo_context.md](docs/ai/repo_context.md)、IDE・モデル・接続の設定は[設定ガイド](docs/ai/config-templates/README.md)に従い、各利用者の環境で管理する。

共通の編集元は`skills/`、`runtime/`、`registry/`、`harness/`と知識本文・カタログである。[共通ソースの同期](docs/ai/integration.md#common-core)はminiから登録された共有ファイルを各リポジトリへ渡す。fullの科学計算依存、lock、コンテナ設定と、各研究のデータ・成果物・利用者設定はそれぞれの保存先で管理する。

APIキー・認証情報は利用者本人のSecretまたはローカル設定へ置く。`data/`、`outputs/`、`artifacts/`、`.agents/state/`などの管理範囲は[.gitignore](.gitignore)にある。
