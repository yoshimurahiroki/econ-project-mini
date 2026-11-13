# Japanese economics writing profiles

Profile family: academic-ja. Language: Japanese.

## Principles

Search for and read the relevant passage and its surrounding section, pages, slides, figures and tables in original sources before composing or revising. Sources include papers and slides from the five leading economics journals published since 2020, major economics handbooks, review articles and guides, economics textbooks, and economics course materials, including lecture notes, course slides and handouts. Map every element of content selection, argument structure, style, vocabulary, transitions, sentence endings, placement, design and appearance to its source; borrow and imitate the corresponding material. For Japanese, use corresponding Japanese originals. Make only the adjustments required for the confirmed facts, names, notation, period, quantities, citations, grammar and medium of the current task; retain the current study’s evidence and conclusions. Record source-to-output mappings and adjustments in the existing working record and check every finished element against its source. Search and read further when coverage is missing. Apply this process to all writing, slides and materials, including short edits, single words, translation and existing drafts. Do not create prose or materials, freely paraphrase, invent examples, or fill gaps without sources. Do not import a source study’s empirical conditions or conclusions into the current task. Exclude disclaimers, hedging, concessions, qualifications, ornamentation, cautious or conservative phrasing, ambiguity, redundancy, weak phrasing, supplementary annotations, and not-A, not-A-but-B and equivalent contrastive rhetoric. Avoid exaggeration and abstract value judgments. Select direct, natural academic expressions from the relevant originals while preserving the current task’s scientific facts, definitions, conditions, quantities, uncertainty and attribution; this preservation does not permit the prohibited rhetoric. Do not relabel invented human-facing prose examples as technical examples.

These three profiles contain the samples adopted from the user’s uploaded manuscript. Read the complete selected sample and ground adopted Japanese expressions and visual elements in corresponding Japanese originals. The body files retain the uploaded Japanese prose. Equations, mathematical variables and Greek letters use LaTeX notation. Keep selection instructions in this index.

## Select a profile

| Writing task | Profile ID | Complete sample |
|---|---|---|
| Explain an institution, identification, estimates and policy calculations | `academic-ja-childcare-employment` | [夕刻預かり事業と母親の就業](childcare-employment.md) |
| Explain a choice model, identification, estimation and counterfactual demand | `academic-ja-attention-plan-choice` | [料金プラン選択における注意の推定](attention-plan-choice.md) |
| Review empirical studies through their settings, methods and estimates | `academic-ja-equipment-subsidy` | [設備更新補助の投資効果](equipment-subsidy.md) |

Each row is a separate registered writing profile and example. Use `academic-ja.` followed by the filename stem as the example ID. Select the complete sample closest to the current writing task.

```sh
python scripts/route_registry.py read academic-ja-attention-plan-choice.all --format compact
python scripts/route_registry.py read econ-writing:compose --user-profile academic-ja-equipment-subsidy --stage compose --format compact
```
