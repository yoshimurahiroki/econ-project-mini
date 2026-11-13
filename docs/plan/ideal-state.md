# 理想状態の設計書

## 目的

Terra クラスのモデルが、問題の発見・設定、経済学的定式化、判断、自律実行、分析・解釈、資料作成までを、最小の読み込みと最小の往復で高品質に完了するハーネスを、正本 econ-project-mini に実現する。構造を作り替える権限は利用者から付与済みである。この文書は到達点と優先順位を定め、手順は [work-procedure.md](work-procedure.md) が担う。

## 優先順位の原理

ハーネスの費用は「1回の費用 × 発生頻度」で決まる。変更案は、この費用の削減量を研究能力への影響で割った順に実施する。研究能力（データ取得、推定、均衡計算、図表、論文、スライド、企業価値評価、再現性）は全案で維持する。要件7が保護する対象は研究機能である。

## 費用の測定値（87d54bb 起点）

| 階層 | 項目 | 測定値 |
| --- | --- | --- |
| 毎ツール呼び出し | `PreToolUse` と `PostToolUse` の起動 | 各 0.12〜0.15秒（Python 起動と3,016行のモジュール読み込み）、注入3B、matcher 指定なしで全ツールに登録 |
| 毎ターン | `UserPromptSubmit` | 注入約0.8KB |
| 毎ターン | Stop レビュー | 依頼文2.2KB と、CORE・PROSE・finish を読む新規サブエージェント1体のモデル呼び出し |
| 毎タスク | 入口ステージの読み込み | 操作あたり約11〜12KB（CORE 4KB、PROSE 約10KB、Skill、research 節）。ハッシュ・オフセット・`--seen` の読み取り手順を伴う |
| 要求時 | 知識基盤 | 335ファイル 3.6MB。`catalog.json`（952KB）は索引で、単位の本文を複製しない |
| 要求時 | 文書 | `docs/ai/` 手書き5ファイル、計約80KB |

## 構造の測定値

- 操作18、条件297（本文が一意の条件は254）、規則614（操作と条件から前提規則を含めて到達できる規則375、残り239はプロファイル・見本・設定雛形などID指定で読む規則）。
- ハーネス Python 23ファイル 1.55MB。制御層（`codex_hooks` 3,016、`paragraph` 1,628、`argument` 1,002、`policy_assets` 890、`local_checks` 745、`native_check` 524、`requirements_check` 473、`experience` 459、計8,737行）と研究実行層（`state` 4,178、`research_artifacts` 2,742、`research` 1,980、`research_gallery` 1,249、`research_evidence` 886、`research_meetings` 865、`reproduction` 762、計12,662行）に分かれる。
- `state` と `codex_hooks` が相互に取り込み合う。`paragraph`、`argument`、`policy_assets` は研究実行層（`state`、`reproduction`、`research_evidence`）から呼ばれる。
- 呼び出し元を持たない定義は607件中2件（33行）。削除余地は小さく、改善の主眼は費用の階層ごとの配置換えと責務の分離にある。
- エージェント定義は役割名（`lead`、`implementer`、`retriever`、`specialist`、`reviewer`）とモデル名（`terra`＝implementer、`luna`＝retriever、`astra`＝specialist）の二系統で重複する。
- プラグイン定義は `plugin.json` と `.codex-plugin/plugin.json` の2つで、本文の差は拡張欄の有無だけである。
- この実行環境にインストール済みの ERS プラグインは存在しない。同期先 econ-project はこのセッションの GitHub 範囲外にある。

## 設計原則

1. **頻度の高い費用から削る。** ツール呼び出し、ターン、タスク、要求時の順に配置を見直す。
2. **規則は1箇所に置く。** 本文は所有者ファイルに1つだけ置く。ホスト別の入口と pin 文字列は、所有者への参照またはそのハッシュで表す。
3. **登録簿を唯一の配線元にする。** 索引、入口、manifest、エージェント定義、プラグイン定義を登録簿から生成する。
4. **読み込みは完全本文を上限付きで返す。** `read` が操作とステージに対する完全本文を返し、重複検出のハッシュは内部で扱う。モデルが管理する手順を持たせない。
5. **経済学的定式化を入口に置く。** ranked pair（直近の問いと最上流の問い）の選択を全操作の最初の判断にする。
6. **借りて真似る規則は PROSE Common output が所有する。** 実在資料への対応づけと最小調整を、文、文章、資料、スライドの全要素に適用する。
7. **anti-defensive を全出力に適用する。** 検査は既存の `scan-text` だけを使い、検査機構を新設しない。
8. **制御層と研究実行層を分ける。** 研究実行層は制御層に依存しない。制御層の各機能は、要件を満たす最も単純な機構に置き換える。

## 目標構造

```
AGENTS.md → CORE（権限・入口・完了） → PROSE（表現・Common output）
              DECIDE（問題選択・定式化・解釈）  ← CORE の経済学者の役割と一本化
registry/{operations,resources,placements}.json   ← 配線の正本
  生成: 索引、Skill の操作一覧、ホスト別入口、policy_manifest、エージェント定義、プラグイン定義
skills/<7 Skill>/SKILL.md + references/            ← モード固有の本文だけ
harness/research/*   研究実行層（state、research、artifacts、evidence、reproduction、meetings、gallery）
harness/control/*    制御層（hooks、policy、checks、paragraph、argument、experience）。研究実行層から参照されない
```

## 到達基準

1. Stop レビューは、利用者向けの文章または成果物を作ったターンだけで起動する。非該当ターンの追加モデル呼び出しは0回。
2. `PreToolUse` は書き込み・外部作用のあるツールだけで起動し、`PostToolUse` は状態に記録するツールだけで起動する。読み取りツールの起動は0回。
3. 入口ステージの読み込みを操作あたり6KB以下にする。
4. 手書きファイル間の120文字以上の完全一致文を0にする。
5. pin 文字列の複製を0にし、PROSE Common output のハッシュ照合に置き換える。
6. 条件の本文重複を0にする（現状43件の統合余地）。
7. エージェント定義を役割ごとに1ファイルへ統合し、モデル ID と推論強度は利用者の現行値を保持する。
8. `plugin.json` の重複を1つの生成元に統合する。
9. 研究実行層から制御層への取り込みを0にする。
10. `docs/ai/` の手書き文書を3ファイル以下にする。
11. 運用文書の `scan-text` 検出を0にする（規則一覧そのものを目的とする `PROSE.md` と `prose_rules.md` を除く）。
12. `export_project.py --check`、3種の書き出し、全操作・全ステージの `route_registry.py read` が通る。
13. 恒久テスト、常設監査、ベンチマーク、監視基盤を新設しない。

## 承認が必要な変更

次の2件だけが CORE の既存規則を変更する。利用者の承認を得てから実施する。
- Stop レビューの起動範囲を絞る（CORE の「ターンごとに1回の独立 Stop レビュー」を「利用者向けの文章または成果物を作ったターン」に限定する）。
- 読み取り手順の簡素化に伴う CORE 第2項の文言変更。

上記以外の変更は付与済みの権限で実施する。

## 非目標

分析パッケージ、Quarto、LaTeX を要する実行、研究計算の数値結果を変える変更、利用者が設定したモデル ID の変更は含めない。econ-project の変更は、同期差分の提示までとする。
