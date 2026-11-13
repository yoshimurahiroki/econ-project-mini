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

## 実施結果

| 段階 | 結果 | コミット |
| --- | --- | --- |
| 1 Stop レビューの範囲限定 | 完了。200文字以上の回答、または `.md/.tex/.qmd/.txt/.html/.docx/.pptx/.pdf/.bib` を名指す回答のターンだけで起動。短い応答のターンは追加モデル呼び出し0回。CORE 完了節を同範囲に更新。 | `469b184` |
| 2 ツール呼び出しフック | 完了。`hooks/check.py` が、ネイティブのファイル読み取りツールの `PreToolUse`・`PostToolUse` を、再注入待ちがなく失敗応答でない場合に即時終了。読み取り呼び出し 0.13秒 → 0.04秒。書き込み系は従来の経路。 | `82ec5b7` |
| 3 入口読み込み | 完了。入口ステージに他ステージ用の PROSE 節を引き込んでいた `requires` を除去。18操作の平均 13.8KB → 9.7KB、econ-writing 16.9KB → 9.7KB。全18操作×5ステージの読み取り90回が成功。読み取り手順（ハッシュ・オフセット）の文言は現行のまま維持。 | `df9d512` |
| 4 pin 文字列のハッシュ化 | 見送り。`PRIMARY_*_RULE` は worker 用 instruction packet の接頭辞で、保存済みの段落契約・タスクの `instruction_context` と文字列一致で照合される。置換すると保存済みの実行を再開できなくなる。 | |
| 5 エージェント統合 | 見送り。モデル名の定義（terra・luna・astra）は `scripts/setup_ide_mcp.sh` の役割表、`resources.json`、`policy_manifest.json` に結び付いており、統合は 30KB の設定生成スクリプトの書き換えを要する。削減効果は読み込み量に現れない。 | |
| 6 ランタイム文書の統合 | 見送り。`EXECUTION.md` と `DECIDE.md` は入口ステージで読まれず、統合しても毎タスクの読み込みが変わらない。 | |
| 7 条件の統合 | 見送り。条件名はコードと登録簿が参照する識別子で、本文が同一の43件を統合しても読み込み量が変わらない。 | |
| 8 制御層の分離 | 見送り。`state` と `codex_hooks` の相互取り込みは実行時の費用を生まない。研究実行層の保存済み状態との互換を保つため、モジュール移動を行わない。 | |
| 3b 全ステージの読み込み | 完了。入口以外のステージが CORE と PROSE Common output を再配信していた動作を廃止し、`read --restore` で文脈喪失・引き継ぎ・モデル変更の後に再配信する。各 PROSE・research・execution・team の節を最初に必要なステージだけに割り当て。5ステージ合計の平均 60,971B（基準 `c39d4a4`）→ 26,403B。入口で配信済みの節（CORE、Common output、Skill 入口、research の入口節）は以降のステージで再配信せず、プロファイル選択表は contract のみで配信。18操作すべてで、基準の `required_rules` の和集合が全ステージ（`--restore` 含む）に残る。入口以外のステージは省略を `omitted` 欄と冒頭の1行で示す。final-form card は専用見出しに移し、どのステージも配信しない（Stop レビューは従来どおりマーカーで取得）。CORE 第2項と索引の文言を更新。 | `8af632b`、`b42153d` |
| 8b 未使用コード | 完了。呼び出し元のない `local_checks.UTF8Text` と未使用の `codecs` 取り込みを削除。`gallery_items` は研究例が呼ぶ公開関数のため維持。 | |
| 9 文書の集約 | 見送り。`docs/ai/` の各文書は `resources.json`・`placements.json`・`operations.json` に登録され、操作の必須規則として読まれる。`scan-text` の検出の大半は、ツールの挙動を規定する技術文の否定表現であり、意味を変えずに書き換えられる箇所だけを今後の編集で修正する。 | |

## 実行環境での検証

`pyproject.toml` が指定する版に合わせ、conda-forge から micromamba で Python 3.12.13、R 4.5.3、Quarto 1.9.38、Pandoc 3.8.3、Julia 1.13.3、DuckDB 2.0.0 を導入し、TeX Live 2026（CTAN の `install-tl`、LuaLaTeX・Beamer・日本語組版を含む）と PyPI の分析パッケージ（pyblp、linearmodels、pyfixest、econml、DoubleML、StatsPAI など）を追加した。

| 検証 | 結果 |
| --- | --- |
| 研究例 housing、charging、subscription の `run.py` | 成功（`housing-transport-v1`、`charging-merger-v1`、`subscription-allocation-v1`） |
| subscription の資料生成と Quarto による HTML 出力 | 成功 |
| 同資料の Quarto + LuaLaTeX による PDF 出力（日本語） | 成功 |
| `tex/paper/ecta_template.tex` と `tex/slides/main.tex` の LaTeX ビルド | 成功 |
| Julia のパッケージ導入（pkg.julialang.org） | 成功 |
| 研究例の資料生成と Quarto 出力（housing・charging・subscription の日本語 14 件、英語 5 件の bundle を HTML・PDF） | 全件成功。subscription の日本語論文 PDF は修正前に失敗していた（`econsocart` が Babel の読む見出し名を定義せず、`\begin{document}` で停止）。論文 PDF から Babel の言語指定を外し、`meeting_template.qmd` の `\babeladjust` を Babel 読み込み時だけ実行する形にして解消。 |
| スライドテンプレートの `mathserif` クラスオプション（beamer が廃止予定と警告） | `\usefonttheme[onlymath]{serif}` に置換。描画は同一。生成器 `research_artifacts.py` の置換元も更新。 |
| `ruff` の F 系検査 | 未使用 import 7件を削除。残る6件は依存の存在確認を目的とする import で維持。 |
| 書き方の参照文書の否定表現 | `result-artifacts.md`（23件 → API フィールド名由来4件）、`practice.md`（8件 → 0件）、`paper-workflow.md`（5件 → 0件）、`artifact-writing.md`（4件 → 0件）、`integration.md`（28件 → 10件）を肯定形に書き換え。`integration.md` の借用規則の複製は PROSE Common output への参照に置換。 |
| 残る `scan-text` 検出（技術文書） | `harness/state.md` 44件、`designs.md` 43件、`implementation-data.md` 36件、`equity-models.md` 27件、`reproducible-workflow.md` 17件、`docs/ai/config-templates/README.md` 17件。ツールの挙動と数式の条件を規定する文が大半で、文ごとに意味を確認して書き換える。 |
| Markdown の相対リンク 782件 | 壊れたリンク0件（検出2件は数式の誤検出） |
| 研究例 equipment と commuting（ruspy と estimatr 2.1.0 の固定版を `git clone` で取得して導入） | 成功（`equipment-renewal-v1`、`commuting-market-v1`）。日本語・英語の資料 bundle 8件を HTML・PDF で出力し、全件成功 |
| `pixi` の導入と TinyTeX の導入 | 未実行。`github.com` のリリース配布と `prefix.dev` が拒否される（`git clone` は通る）。conda-forge と CTAN の直接導入で代替 |

## 実施順

段階1 → 2 → 3 → 4 → 5 → 6 → 7 を順に進める。段階8は段階7の後、段階9は段階4の後に独立して進められる。段階1と3は承認を得るまで保留し、その間に段階2、4、5、6、7を先行できる。
