# Japanese economics writing profile

Profile family: academic-ja. Language: Japanese.

## Use

Form conventions for Japanese research documents and slides. [WRITING](../../runtime/WRITING.md) governs expression, exemplars and completion. Use only the sections required by the artifact.

## 1. Characters and punctuation

- Papers, notes and briefs: 「，．」. Slides: 「、」 and endings from the selected slide passages.
- Half-width Latin letters, numerals, operators and intervals; full-width Japanese parentheses. Space between a number and a Latin unit; 年・月・人・件・円・% follow the number directly.
- Quantities in digits; grouping commas from 4 digits, minus 「−」, range 「–」.

## 2. Numbers

- Estimates, standard errors and intervals share scale and decimals; each table column has one precision. Round once from saved values; use p < 0.001 below that value.
- Proportion changes in percentage points; give a monetary result's currency, price base year and scale at first use.

## 3. Terms

- One standard term per concept across all output; introduce a needed abbreviation once as 「日本語術語（原語，略語）」.
- Use 推定値 for a number, 推定結果 for results and 推定量 for an estimator; 処置群, 対照群, 識別, 厚生. Retain software and variable spellings; use データ, モデル, パラメータ, クラスター.

## 4. Symbols and equations

- Use standard notation; define work-specific symbols at first use. Number equations throughout and cite 式(1), 表1, 図1, 第2節.

## 5. Tables and figures

- Tables: numbered title, column numbers (1), (2), coefficient and parenthesized standard error on consecutive rows, observations and specification rows below. X marks included blocks. Portrait, at most 9 columns, horizontal rules, decimal alignment, Panel A/B.
- Table notes give estimator by column and standard-error type in one sentence from saved specifications. Figure notes give saved interval level and type.
- Figures: quantity and unit on axes, labelled intervals, vector PDF, panels a/b/c; common scales for comparisons.

## 6. Citations and references

- 著者（年） as subject, （著者 年） for attribution; two Japanese authors joined by ・, three or more by first author and ほか. List every author in references.
- Articles: author, year, title, journal, volume, issue, pages, DOI. Books: author, year, title, publisher. Working papers: author, year, title, series, number, institution, URL.

## 7. Layout

- Papers: `tex/paper` econsocart, LuaLaTeX, Harano Aji; exhibits after first citation, centred footer page numbers.
- Slides: `tex/slides`, 16:9, metropolis, Waseda colours; body/tables/captions 32 pt, headings 36 pt, title 44 pt, lower-right page number. One claim, exhibit or equation and quantitative reading per slide; overflow continues at the same size.

## 8. Genres

- [Papers](../../skills/econ-writing/references/paper-workflow.md), [talks and materials](../../skills/econ-writing/references/artifact-writing.md), [proposals and pre-analysis plans](../../skills/econ-writing/references/proposals.md).
- Referee responses: comment, response, exact changed location. Briefs: conclusion and magnitude, evidence, mechanism, action.
