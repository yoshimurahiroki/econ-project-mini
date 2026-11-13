# 理想状態の設計書

## 目的

Terra クラスのモデルが、問題の発見・設定、経済学的定式化、判断、自律実行、分析・解釈、資料作成までを、読み込み量を抑えて高品質に完了できるハーネスを正本 econ-project-mini に置く。この文書は到達点を定め、手順は [work-procedure.md](work-procedure.md) が担う。

## 現状の測定値（87d54bb 起点、整理5コミット適用後）

| 項目 | 測定値 |
| --- | --- |
| 操作 | 18、条件297 |
| 操作の入口ステージで読む量 | 約11〜12KB（CORE 4KB、PROSE 約10KB、Skill、research 節） |
| `harness/*.py` | 23ファイル 1.55MB、`state.py` 4,178行、`codex_hooks.py` 3,016行 |
| 呼び出し元を持たない定義 | 607中2件（33行） |
| `registry/*.json` | 3ファイル 441KB |
| 知識基盤 `skills/econ-knowledge` | 335ファイル 3.6MB |
| 入口ファイル | ホスト別12ファイルが同一の全文規則（約1.9KB） |
| `docs/ai/` | 8ファイル。`integration.md` 29KB、`resources.md` 21KB、`plugin-integration.md` 14KB |
| 表現規則の既存スキャン | `integration.md` 28件、`result-artifacts.md` 23件、`practice.md` 8件 |

## 設計原則

1. **規則は1箇所に置く。** 各規則の本文は1つの所有者ファイルに置き、他は所有者への参照にする。ホスト別の入口ファイルは各ホストが1つだけ読むため、生成物として全文を持つ。
2. **登録簿を唯一の配線元にする。** `registry/operations.json` と `resources.json` から索引、Skill の操作一覧、入口、manifest を生成する。手書きの配線は残さない。
3. **読み込みは段階で絞る。** entry は分類、contract は問いと方法、compose は実行、review は解釈と修復、finalize は保存と納品に必要な本文だけを返す。各ステージが読む本文に重複を持たない。
4. **経済学的定式化を入口の判断に組み込む。** CORE の「ranked pair」と DECIDE の深掘り・比較・行動選択が、全操作の最初の判断になる。容易な表面的問題を採らず、結果が決定を変える上流の問いを選ぶ。
5. **借りて真似る規則は PROSE Common output が所有する。** 文、文章、資料、スライドの内容、構成、語彙、文末、配置、デザインを実在資料から対応づけ、事実に合わせる最小の調整だけを行う。
6. **anti-defensive を全出力に適用する。** 思考・判断・行動・文章の全てで PROSE の除外規則に従い、科学的に必要な情報は内部記録に保持する。検査手段は既存の `local_checks.py scan-text` とし、検査機構は新設しない。
7. **機能の保存。** 研究能力（データ取得、推定、均衡計算、図表、論文、スライド、企業価値評価）と再現性（状態管理、再利用、依存伝播）を維持する。構造の簡素化は重複・配線・読み込み範囲に限る。

## 目標構造

```
AGENTS.md → runtime/CORE.md → runtime/PROSE.md
              │                  └ Common output（借りて真似る規則の正本）
              ├ DECIDE.md   問題選択・定式化・解釈
              ├ EXECUTION.md 実行・失敗伝播
              └ TEAM.md     委任・再開・レビュー
registry/operations.json ─ resources.json ─ placements.json（配線の正本）
        └ 生成: docs/ai/compiled_ai_skills.md、Skill の操作一覧、入口ファイル、policy_manifest.json
skills/<7 Skill>/SKILL.md（操作一覧と固有手順のみ）+ references/（モード固有の本文のみ）
harness/（実行・状態・成果物・検証コード。依存関係を持つ処理を保持）
profiles/、tex/（実在資料に基づく見本とテンプレート）
```

## 到達基準

1. 入口ステージの読み込みを操作あたり8KB以下にする。現状は約11〜12KB。
2. 借りて真似る規則の全文を、PROSE Common output、`final-form-card`、ホスト別入口ファイル（生成物）、`project_instructions.txt`（生成物）だけが持つ。
3. 手書きファイル間の完全一致文（120文字以上）を0にする。現状は生成物とホスト別入口を除き、`PROFILE.md` 内の文を含む約2KB。
4. `docs/ai/` の手書き文書を、保守に必要な役割ごとに1ファイルへ集約し、`integration.md` と `plugin-integration.md` の重複記述を解消する。
5. `scan-text --surface final` の検出件数を、規則一覧を目的とする `PROSE.md` を除く運用文書で0にする。
6. 登録簿から生成する全ファイルについて `export_project.py --check` が終了コード0を返し、3種の書き出し（task、deployed、plugin）のリンクが全件実在する。
7. 恒久テスト、常設監査、ベンチマーク、監視基盤を新設しない。
8. 同期先 econ-project へ、`sync_common_core.py` の共通パス集合を保ったまま反映できる。

## 非目標

分析パッケージ、Quarto、LaTeX を要する実行は含めない。研究計算の数値結果を変える変更は含めない。econ-project 側の変更は、同期用の差分提示までとする。
