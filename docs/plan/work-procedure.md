# 作業手順書

[ideal-state.md](ideal-state.md) の到達基準を、依存の少ない順に実施する。各段階は「編集 → 再生成 → 検証 → 1コミット」で完結し、`ccr-0532f95d-npvlpj` へ push する。

## 共通ループ

1. 所有者ファイルを編集する（登録簿、`runtime/*.md`、Skill、参照）。
2. `python3 scripts/export_project.py --generate-entries` で生成物を更新する。
3. `python3 scripts/export_project.py --check` が終了コード0を返すことを確認する。
4. 本文を変えた段階では、`--task econ-writing --mode compose`、`--format deployed`、`--format plugin` を scratchpad に書き出し、追加・変更したリンクの実在を確認する。
5. 手書き文書の変更後に `python3 harness/local_checks.py scan-text --surface final --input FILE --dictionary quality/prose_rules.json` を実行し、検出0を確認する。
6. 1段階1コミット。件名は短い英語の命令形とする。

## 段階0　基準値の記録

- 操作ごとの入口ステージの読み込み量: `python3 scripts/route_registry.py read OP --stage entry --format compact | wc -c`（18操作）
- 重複文: 120文字以上の完全一致文を数える Python 1回実行（スクリプトは保存しない）。
- 表現規則の検出件数: 運用文書ごとに `scan-text`。
- 受け入れ: 数値を作業ログ（コミット本文）に残す。

## 段階1　規則の単一所有の完了

1. `harness/meetings.md` のテンプレート固有の段落から、PROSE と重なる記述を削る。
2. `quality/prose_rules.md` を `prose_rules.json` と PROSE との重なりで整理し、規則一覧の正本を1つに決める。
3. `PROFILE.md` 3ファイルの類似文（資料の選び方、除外表現）を PROSE への参照に置換する。
4. `harness/policy_assets.py` の `PRIMARY_EXPRESSION_RULE` と `PRIMARY_STYLE_RULE` は、`paragraph.py` の検証が参照する。検証が確認する文字列を PROSE Common output への参照付き短文に改め、両ファイルを同時に更新する。
5. `docs/ai/economics-writing-comparison.md` の内容を、`integration.md` 内の該当節または参照として統合する。
- 受け入れ: 到達基準2と3。

## 段階2　入口ステージの縮小

1. 入口ステージが返す本文を列挙する（`bodies` キー）。`research#turn-the-question-into-an-operation`、CORE、PROSE の各節、Skill が対象。
2. entry で必須の本文を CORE と Skill の入口に限り、PROSE の節（argument、connect、profile、language、finish）を contract・compose・review の各ステージへ移す。移す節は `registry/operations.json` の `required_rules` と `reading_stages`（`resources.json`）で指定する。
3. `finish-the-passage` を finalize と review に限定する。
4. 18操作で入口の読み込み量を再測定する。
- 受け入れ: 到達基準1。読み込み順序の変更が CORE の「Common output を一度読む」規則と整合することを確認する。

## 段階3　経済学的な判断の入口への統合

1. `DECIDE.md` の「Turn the question into an operation」と CORE の Economist role を読み、同じ手順が2箇所に分かれている部分を CORE に一本化する。
2. 各 Skill の入口（econ-design、econ-data、econ-literature、econ-review、project-work）に、その Skill 固有の「主体・目的・選択・制約・識別・決定」の問い方を1項ずつ置く。共通部分は CORE への参照にする。
3. 実際の呼び出し例（依存不要の `route_registry.py read` と `resolve`）で、各操作が最上流の問いを選ぶ手順に到達することを確認する。
- 受け入れ: 全操作の入口で、ranked pair の受け渡しが1回だけ記述される。

## 段階4　Skill と参照の整理

1. `skills/econ-data/references`（`implementation-*.md` 8ファイル、`equity*.md`）で、`implementation.md` と `implementation-engines.md` の選択表が同じ内容を持つ箇所を特定し、選択表の所有者を1つに決める。
2. `skills/econ-design/references/designs.md`（77KB）の見出し構造を確認し、参照時に節単位で読める構造にする。
3. `skills/econ-writing/references` の `paper-workflow.md`（48KB）、`result-artifacts.md`（56KB）で、PROSE と重なる記述と、`scan-text` の検出箇所（`result-artifacts.md` 23件）を修正する。
4. 修正した節ごとに `route_registry.py read` で到達性を確認する。
- 受け入れ: 到達基準3と5。

## 段階5　文書の集約

1. `docs/ai/integration.md`（28件の検出）と `plugin-integration.md` の内容を比較し、配置・同期・書き出し・フック設定の各節を1ファイルに集約する。
2. `docs/ai/resources.md`（生成物）の参照元を確認し、生成の要否を決める。
3. `README.md` の記述を、現行の入口（AGENTS.md → CORE → PROSE → 索引）と一致させる。
- 受け入れ: 到達基準4と5。

## 段階6　ハーネスコードの構造整理

1. 呼び出し元を持たない2定義（`local_checks.py: UTF8Text`、`research_artifacts.py: gallery_items`）を、全リポジトリの参照検索で確認して削除する。
2. 1,000行超のモジュール（`state.py`、`codex_hooks.py`、`research_artifacts.py`、`research.py`、`paragraph.py`）について、責務ごとの節構成を図にし、重複する補助関数（パス検証、原子的書き込み、ハッシュ）を共通モジュールへ寄せる候補を列挙する。
3. 候補のうち、呼び出し元が同一モジュール内に閉じ、実行しなくても依存関係を静的に確認できるものだけを移す。
4. フックの注入量を `hooks/check.py` で各イベントについて測定し、Stop のレビュー依頼文（現在 2,227B）、UserPromptSubmit（約0.8KB）、SessionStart（約0.8KB）の内容を、受け手が行動を変える情報に限る。
- 受け入れ: 研究実行の入口（`research.py`、`state.py`）の公開関数名と引数を維持する。

## 段階7　テンプレートとプロファイル

1. `tex/paper`（6ファイル）、`tex/slides`（5ファイル）を読み、ビルド設定の重複を整理する（ビルドは実行しない）。
2. `profiles/top-five-en`（26ファイル）と `profiles/academic-ja` の見本は、採択済みの本文として維持し、`PROFILE.md` の選択表だけを整理する。
3. `.github/ISSUE_TEMPLATE`、`docs/issue`、`.vscode`、`.devcontainer` の設定を、現行の入口と一致させる。
- 受け入れ: 本文の見本を変更しない。

## 段階8　エージェント構成の確認

1. `.codex/agents`（7ファイル、簡約形）と `references/repository-policy/.codex/agents`（8ファイル、配備用の詳細形）の役割を `docs/ai/integration.md` に1節で記す。
2. モデル ID と推論強度の設定は利用者が管理する値として扱い、変更の要否を利用者に提示する。
- 受け入れ: 両系統の違いが文書で説明される。

## 段階9　同期と最終検証

1. `python3 scripts/sync_common_core.py --source . --target ../econ-project` を読み取り比較で実行し、差分を提示する（`--apply` は利用者の指示後）。econ-project は本セッションの GitHub 範囲外にあるため、差分の確認は利用者の環境で行う。
2. 全 Skill について `route_registry.py read` を各ステージで実行し、本文の欠落がないことを確認する。
3. 到達基準の測定値を段階0と比較し、結果をコミット本文と最終報告に記す。
4. 恒久テスト、監査、ベンチマークを新設しない。作業で作った一時スクリプトは scratchpad に置き、リポジトリに追加しない。

## 実施順と所要の目安

段階1 → 2 → 3 → 4 → 5 の順に進める。段階6〜8は段階5の後に独立して実施できる。段階9は最後に1回行う。各段階の変更範囲は登録簿と生成物で閉じており、途中の段階で止めても `--check` は通る。
