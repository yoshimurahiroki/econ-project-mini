---
name: econ-data
description: Acquire, transform, estimate and reproduce economic data and results; implement and simplify research code through its existing owners and execution paths. Execute BLP, NFXP, MPEC, structural GMM, dynamic games and equilibrium counterfactuals. Evaluate Japanese and global equities with free financial data, sustainable cash flow, valuation and news updates.
---

# Research data

This skill carries step 5 of the [economist's procedure](../../runtime/ECONOMIST.md): run the design from the worksheet with the existing scripts.

Preserve the adopted objective, feasible set, transfers and mechanism in the calculation. Save its changed economic premise, responses, equilibrium or optimum, and the mechanism selecting the action with their source definitions for the decision and writing steps.

0. **Procedure.** Follow the [empirical procedure](references/empirical.md) for the requested estimand. Select the determining estimate and inference under ECONOMIST Economic priority and Requested work; reuse saved results and compact worksheet entries.
1. **Data.** Clean, reshape, join, construct variables, describe and plot through the [data preparation procedure](references/data-preparation.md) (audit template `templates/data_audit.py`; P0 rules without exceptions); acquire through [research data](references/research-data.md).
   Rules without exceptions: everything runs in code and received files are never edited; the unit and key of every table are written first; imputation, deletion of outliers or records, winsorizing, value corrections, controls, aggregation rules, base years and weights come only from worksheet section 4 or [user] (imputation, outlier deletion, winsorizing and corrections only from [user] or the source's documentation), never from the data; every join declares its relationship and is checked for missing keys, matches and row counts; derived values are new columns; a evident input or calculation error under Economic priority is repaired at its producer; preserve the adopted target and source definitions.
2. **Estimation.** Run the selected method from the [implementation table](references/implementation-engines.md) with the matching script: `scripts/research_causal.py` (and `research_causal.R`, `research_rct.R`), `research_markets.py`, `research_dynamic.py`, `research_macro.py`, `research_macro_extended.py`, `research_dsge.py`, `research_numerics.py`. Specification fields and calls are in [implementation calls](references/implementation-calls.md); worked runs in [implementation examples](references/implementation-examples.md).
3. **Projects.** Multi-stage work runs through `python3 harness/research.py --root . research.json` ([research runner](../../harness/research.md)).
4. **Equity valuation.** The `equity` mode follows [equity](references/equity.md).
5. **Return.** Save results with their inputs, sample, units, estimator and inference; write the determining estimate and inference into the worksheet for step 6, then complete the requested answer.

The general procedure is in the [data workflow](references/workflow.md).

<!-- BEGIN GENERATED MODES -->
## Registered operations

- `execute`: Acquire, transform, join, calculate, estimate or change research data and code.
- `equity`: Evaluate Japanese, US and overseas equities from public filings, IR and market observations; estimate competition, compute sustainable cash flows, reverse valuation, after-tax investment decisions and news-driven changes.
<!-- END GENERATED MODES -->
