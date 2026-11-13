# 作業手順書

[ideal-state.md](ideal-state.md) の到達基準を、費用削減量が大きく研究能力への影響が小さい順に実施する。各変更は「編集 → 再生成 → 検証 → 1コミット」で完結し、`git revert` で単独に取り消せる。

## 共通ループ

1. 所有者ファイル（登録簿、`runtime/*.md`、Skill、参照、コード）を編集する。
2. `python3 scripts/export_project.py --generate-entries` で生成物を更新する。
3. `python3 scripts/export_project.py --check` が終了コード0を返すことを確認する。
4. 本文または配線を変えた変更では、`--task econ-writing --mode compose`、`--format deployed`、`--format plugin` を scratchpad に書き出し、リンクの実在を確認する。
5. 全18操作の全ステージで `python3 scripts/route_registry.py read OP --stage S --format compact` が成功することを確認する。
6. 手書き文書の変更後に `python3 harness/local_checks.py scan-text --surface final --input FILE --dictionary quality/prose_rules.json` を実行する。
7. フックを変えた変更では、`hooks/check.py` に各イベントのサンプル入力を渡し、応答 JSON と起動回数を確認する。
8. コミット件名は短い英語の命令形とする。一時スクリプトは scratchpad に置き、リポジトリに追加しない。

## 段階0　基準値の再記録

操作ごとの入口読み込み量、重複文数、`scan-text` 検出数、フックの起動時間を測り、コミット本文に残す。

## 段階1　Stop レビューの範囲限定 【承認が必要】

- **費用と頻度**: 毎ターン、追加モデル呼び出し1回とサブエージェントによる CORE・PROSE・finish の読み込み。
- **保持する機能**: 利用者向けの文章・成果物に対する独立レビュー。
- **手順**: `codex_hooks.py` の `_review_final_prose` が、ターン中に作成・編集された利用者向け成果物のパスと最終回答の文章を既に受け取る。この情報から「文章または成果物を作ったか」を判定し、該当しないターンは `None` を返す。CORE 完了節の第3項を同範囲に書き換える。
- **検証**: 判定が真・偽になる2種のサンプル入力で Stop の応答を確認する。
- **ファイル**: `harness/codex_hooks.py`、`runtime/CORE.md`、生成物。

## 段階2　ツール呼び出しフックの絞り込み

- **費用と頻度**: 全ツール呼び出しごとに2回の Python 起動（各 0.12〜0.15秒）。
- **保持する機能**: 書き込み・外部作用に対する権限確認と、操作結果の記録。
- **手順**:
  1. `_tool_effect` が返す分類（read、write、external）を一覧にする。
  2. `PostToolUse` が状態に書き込む条件（`bind-operation` を含む）を一覧にする。
  3. `hooks/hooks.json` の `PreToolUse` と `PostToolUse` に `matcher` を設定し、読み取りツールを除く。ホストの matcher はツール名の正規表現であるため、分類に対応するツール名集合を登録簿で定義して生成する。
  4. 読み取りツールの入力を `hooks/check.py` に渡し、起動されないことを確認する。
- **ファイル**: `hooks/hooks.json`、`placements.json`、`codex_hooks.py`（分類表）。

## 段階3　入口読み込みの縮小と読み取り手順の簡素化 【CORE 文言の変更に承認が必要】

- **費用と頻度**: 毎タスク、約11〜12KB とハッシュ管理の手順。
- **手順**:
  1. 入口ステージが返す本文を列挙し、PROSE の各節（argument、connect、profile、language、finish）を contract・compose・review・finalize の各ステージへ振り分ける。振り分けは `required_rules` と `reading_stages` で指定する。
  2. `route_registry.py read` の既定動作を「操作とステージに対する完全本文を返す。上限を超える場合は節単位で分割し、次の呼び出しを示す」に変える。`--seen` とハッシュ引数は内部で扱う。
  3. CORE 第2項を新しい読み取り手順に合わせて書き換える。
  4. 18操作で入口読み込み量を再測定し、6KB以下を確認する。
- **ファイル**: `registry/operations.json`、`resources.json`、`route_registry.py`、`CORE.md`、`compiled_ai_skills.md`（生成）。

## 段階4　規則の単一所有と pin 文字列のハッシュ化

1. `policy_assets.py` の `PRIMARY_EXPRESSION_RULE` と `PRIMARY_STYLE_RULE`、`paragraph.py` の検証を、PROSE Common output 節のハッシュ照合に置き換える。
2. `harness/meetings.md`、`quality/prose_rules.md`、`PROFILE.md` 3ファイルに残る重なりを PROSE への参照にする。
3. 120文字以上の完全一致文を数え、0を確認する。
- **先行確認**: `paragraph.py` の検証が過去の見本を読み込む経路を先に確認し、旧文字列で保存された成果物の読み込みを維持する。

## 段階5　エージェント定義とプラグイン定義の統合

1. 役割名（`lead`、`implementer`、`retriever`、`specialist`、`reviewer`）を正とし、`terra`・`luna`・`astra` をモデル指定の別名として同一ファイルに統合する。モデル ID（`gpt-6-terra` 系）と推論強度は現行値を保持する。
2. `placements.json` のエージェント定義10件を役割ごとの生成に変える。
3. `plugin.json` と `.codex-plugin/plugin.json` を、1つの生成元から出力する。
4. 配備用（`references/repository-policy/.codex/agents`）と本リポジトリ用（簡約形）の差を1節にまとめる。
- **検証**: `--check`、3種の書き出し。

## 段階6　ランタイム文書の統合

1. CORE の「Economist role」と DECIDE の「Turn the question into an operation」の重なりを CORE に一本化する。
2. `EXECUTION.md`（3KB）を CORE の完了節または各 Skill の実行手順へ統合する。
3. `TEAM.md` の再開・使用量集計の節を、必要時のみ読む節に分離する。
- **検証**: 全操作の `required_rules` が統合後の節IDを指す。

## 段階7　登録簿の簡約

1. 本文が同一の条件43件を統合する。
2. 到達できない規則239件のうち、ID指定で読む見本・設定雛形を明示し、残りを精査する。
3. 登録簿から生成できる手書き記述（Skill の操作一覧、入口）の残りを生成に移す。

## 段階8　制御層と研究実行層の分離

1. 制御層8モジュールごとに、機能、要件が必要とする程度、最も単純な機構を表にする。
2. `state` と `codex_hooks` の相互取り込みを、共有部分を `harness/control` 側の小モジュールに切り出して解消する。
3. 研究実行層（`state`、`research`、`research_*`、`reproduction`）から制御層への取り込みを、フック経由のイベント通知だけにする。
4. 公開関数名と引数を維持する。モジュールの移動は `import` 経路の静的確認で検証する。
- **範囲**: 構造変更のみ。研究計算の数値は変えない。

## 段階9　Skill・参照・テンプレート・文書

1. `skills/econ-data/references` で、`implementation.md` と `implementation-engines.md` の選択表の所有者を1つに決める。
2. `designs.md`（77KB）、`paper-workflow.md`（48KB）、`result-artifacts.md`（56KB）を節単位で読める構造に整え、`scan-text` の検出（`result-artifacts.md` 23件、`integration.md` 28件）を修正する。
3. `docs/ai/` を、配備と同期、フックと設定、操作索引の3文書に集約する。
4. `README.md` を現行の入口（AGENTS.md → CORE → PROSE → 索引）に一致させる。
5. `tex/` と `profiles/` は、見本本文を変えずに選択表と設定の重複を整理する（ビルドは実行しない）。

## 段階10　同期と最終検証

1. `python3 scripts/sync_common_core.py --source . --target ../econ-project` を読み取り比較で実行し、差分を利用者に提示する。`--apply` は利用者の指示後に実行する。
2. 到達基準1〜13を段階0と比較し、結果を最終報告に記す。

## 実施順

段階1 → 2 → 3 → 4 → 5 → 6 → 7 を順に進める。段階8は段階7の後、段階9は段階4の後に独立して進められる。段階1と3は承認を得るまで保留し、その間に段階2、4、5、6、7を先行できる。
