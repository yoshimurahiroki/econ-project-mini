# econ-project-mini

Python・R、Jupyter、Quarto、LaTeX と、経済学研究向けの AI 指示をまとめた作業環境のテンプレートです。実行と文書作成の基盤を用意し、分析ライブラリは研究に合わせて追加します。

[econ-project](https://github.com/yoshimurahiroki/econ-project) は、計量経済・因果推論・機械学習のライブラリと Pixi／rv の lock ファイルを含む構成です。mini は基盤中心の依存定義に、Quarto の論文・スライド雛形と LaTeX ビルド補助を備えています。

## 使い始める

```sh
git clone https://github.com/yoshimurahiroki/econ-project-mini.git
cd econ-project-mini
```

AI の指示を使うには、このフォルダーを コーディングエージェント の作業場所にし、[AGENTS.md](AGENTS.md) と[操作一覧](docs/ai/compiled_ai_skills.md)を入口にします。

分析環境と文書ビルドを使う場合は、Docker と VS Code の Dev Containers 拡張を用意し、このフォルダーをコンテナで開きます。Pixi の対象プラットフォームは `linux-64` です。初回セットアップはネットワークからパッケージを取得します。

[Dev Container 設定](.devcontainer/devcontainer.json)から [setup-environment.sh](.devcontainer/setup-environment.sh) が実行され、Pixi 環境、rv による R パッケージ、Jupyter カーネルを準備します。コンテナ内の作業場所は `/workspaces/econ-project` です。以降のコマンドはリポジトリのルートで実行します。

```sh
make help
```

## 分析とコードの作業

Python 側の依存は [pyproject.toml](pyproject.toml)、R パッケージは [rproject.toml](rproject.toml) に追加し、次の入口で環境を更新します。mini には `pixi.lock` と `rv.lock` を同梱していません。

```sh
make sync
make r-install
```

Notebook では、セットアップで登録された Python／R カーネルを選びます。データの置き場所は `data/` で、コンテナでは Docker volume に保存されます。データと生成物の Git 管理範囲は [.gitignore](.gitignore) で定義しています。

コードの検査には、分析環境と分けた `quality` 環境を使います。

```sh
make setup-quality
make quality FILE=scripts/pack_context.sh
```

`make lint FILE=...` は lint、`make format FILE=...` は整形、`make test TEST=...` は指定したテストを実行します。検査対象の選び方は[品質検査の説明](docs/quality-checks.md)を参照してください。

## 論文とスライドを作る

[LaTeX 論文](tex/paper/ecta_template.tex)と [Beamer スライド](tex/slides/main.tex)を編集し、次のコマンドで PDF を作ります。

```sh
make build-paper
make build-slides
```

別の原稿は `PAPER=...`、`SLIDES=...` で指定します。LuaLaTeX と必要に応じて pbibtex を実行し、PDF を原稿と同じディレクトリへ出力します。[ビルド補助](scripts/build_latex.py)は、失敗時に既存の PDF を復元します。

Quarto には[論文用](tex/paper/quarto_template.qmd)と[スライド用](tex/slides/quarto_template.qmd)の雛形があります。論文の共通 PDF 書式は [_quarto.yml](_quarto.yml) にあります。

```sh
make qmd-pdf QMD=tex/paper/quarto_template.qmd
make slides-pdf QMD=tex/slides/quarto_template.qmd
```

## AI に研究作業を依頼する

| スキル | 担当する作業 |
|---|---|
| `econ-design` | 研究質問、モデル、識別・推定設計 |
| `econ-literature` | 文献調査、引用・制度の確認 |
| `econ-data` | データ取得・加工、計算、分析コード、中長期株式評価 |
| `econ-writing` | 執筆、改稿、翻訳、論文の説明 |
| `econ-review` | 主張・成果物の評価と指定範囲の修正 |

依頼には、対象資料、欲しい成果物、変更を許す範囲を添えます。Codex では `$econ-writing` などを指定し、改稿なら `revise`、翻訳なら `translate` のように[操作一覧](docs/ai/compiled_ai_skills.md)のモードを選びます。

共有指示の編集元は [skills/](skills/)、[runtime/](runtime/)、[registry/](registry/) にあり、コーディングエージェント 向けの配置は [.agents/](.agents/) です。書き方のプロファイルと Project に渡す追加資料は [repo_context.md](docs/ai/repo_context.md) で選びます。

ChatGPT では、自分用プラグインとして使う方法と、Project へ指示を手動配置する方法を選べます。

### Economics Research Skills を使う

共通スキルの正本はこのリポジトリの最新 `main` です。`econ-writing` が執筆・改稿・説明・翻訳・媒体変換・文章指導・文体プロファイルを担当し、日本語の説明を組み立ててから短縮する工程を各モードに備えます。

この公開版は、個人用サービスへの接続を含まない独立した配布元です。共通ソースの同期、skill 内で読める参照の生成、プラグインの更新は[配布手順](docs/ai/plugin-integration.md)に従います。

新しく自分用プラグインを作る場合は、[最新ソース ZIP](https://github.com/yoshimurahiroki/econ-project-mini/archive/refs/heads/main.zip) を展開し、`python scripts/export_project.py --generate-entries` で5スキルの参照を生成します。生成した配布物を Plugin Creator に渡して登録し、保存後に本文を読み戻します。公開用manifestには認証付きアプリやMCPの固定接続がありません。

### 中長期の株式評価

`econ-data` の `equity` モードは、日本株・米国株・海外株の開示、IR、ニュース、産業統計から構造的競争力と株主価値を計算します。既存の5スキルを使い、[実行手順](skills/econ-data/references/equity.md)と[経済モデル・文献](skills/econ-data/references/equity-models.md)へ進みます。

PyBLPによる差別化需要と価格競争、容量制約付き数量競争、投資・参入の動学ゲームを、事業別の数量・価格・費用・必要投資から持続的FCFへ接続します。余剰現金、負債、希薄化を反映した適正株価、逆DCF、税・取引費用・予算・代替運用を含む購入・保有・売却、新情報による価値変化を計算します。方法選択・識別・均衡計算・会計の専門知識は同梱リファレンスに収録し、通常分析で個人資料の取得を必要としません。売買需給分析は信用取引残高と裁定取引残高に限ります。

```sh
python -m pip install -r skills/econ-data/scripts/requirements-equity.txt
python skills/econ-data/scripts/equity.py value valuation.json --output result.json
```

SEC・企業IR・公的統計は公開データから取得できます。EDINET・e-Statは利用者本人の無料キーを実行環境のSecretから `EDINET_API_KEY`・`ESTAT_APP_ID` へ渡します。未登録時は登録方法を返し、他の利用者のキーやサービスへ接続しません。ブラウザ版ChatGPTで認証付きMCPを利用する場合は、本人が管理・接続したサービスを選びます。APIキー、原本、評価履歴は各利用者の非公開保存先で管理します。有料API・外部LLM APIは使用しません。

### Project に手動で配置する

プラグインを使えない環境では、Project へ指示ファイルを手動配置します。

文章作成用の ChatGPT Project パッケージは、Python 3.12 で書き出せます。まだ存在しない出力先を指定します。

```sh
python3 scripts/export_project.py --task econ-writing --mode compose --output /tmp/econ-writing-mini-new
```

生成された `PROJECT_INSTRUCTIONS.txt` を Project の指示欄へ貼り、残りのファイルを添付します。条件付き参照、native 配置、他リポジトリへの同期は[統合・配布の説明](docs/ai/integration.md)にあります。

### 作業状態を保存する

作業を再開するために成果物の版・依存関係・停止条件を保存するときは、[ハーネスの状態管理](harness/state.md)を使います。

```sh
python3 harness/state.py --root . init
python3 harness/state.py --root . inspect
```

記録先は Git 管理外の `.agents/state/` です。分担と引継ぎの指示は [TEAM.md](runtime/TEAM.md)、成果物の配置や Git 操作は [publication.md](harness/publication.md) にあります。
