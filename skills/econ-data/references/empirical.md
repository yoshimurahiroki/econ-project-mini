# Empirical analysis, step by step

Use this for steps 4 to 6 of the [economist's procedure](../../../runtime/ECONOMIST.md) whenever data are involved. Use compact worksheet entries and ECONOMIST Economic priority and Requested work to select the delivered result. Run every estimate through code and save it; numbers in the answer come from the saved output. A review strengthens the substantive conclusion from saved evidence under ECONOMIST Economic priority through [review R2–R3](../../econ-review/references/review.md); a requested new estimate activates the execution steps below.

## Step E1. Estimand

```
Estimand:            requested coefficient or causal effect, with population, period and units
Model link:          which parameter or prediction of section 3 it measures
Competing predictions and the estimate that separates them:
Decision threshold:  the action informed by this quantity; for a coefficient-table request, the requested specification and interpretation
```

## Step E2. Data audit

Run the audit of [data preparation P1](data-preparation.md#p1-inventory-and-audit-of-received-files) (`templates/data_audit.py`) and print, before any regression:

```
Unit / time / keys:         unique on (unit, time)? duplicates dropped how?
Coverage:                   units, periods, balanced panel?
Treatment:                  coding, timing (one date or staggered), share treated, switches off?
Outcome:                    distribution, zeros, outliers, units, transformations
Missing values:             per variable and by treatment status
Sample rule:                written before seeing estimates; post-treatment variables excluded from the rule
```

## Step E3. Raw facts

Plot or tabulate before modelling: outcome means by group and period (raw trends around adoption), the first stage in raw form for IV, the outcome against the running variable for RD. Write two lines on what the raw pattern says about assignment and untreated outcome dynamics. Trace the assignment variables through both outcome levels and growth; use the existing data summaries for this economic comparison.

## Step E4. Design and method: decision rules

Choose the row that matches the requested quantity and the economic model of assignment and untreated outcomes. When several rows apply, select their comparison and target population explicitly. Threshold assignment and common timing can support different targets; table order gives each row equal standing.

| Variation | Design | Estimator references |
| --- | --- | --- |
| Random assignment | experiment | difference in means → with strata fixed effects → with pre-registered covariates |
| One adoption date, treated and control groups | 2×2 difference-in-differences | raw difference → two-way fixed effects → + pre-determined controls |
| Adoption dates differ across units (staggered), absorbing | staggered difference-in-differences | two-way fixed effects as rung 1 only → imputation (`pf.did2s`) or `did::att_gt` |
| Treatment switches on and off, or doses differ | treatment paths | `DIDmultiplegtDYN`, `contdid` (R) |
| Eligibility by a threshold of a score | regression discontinuity | `rdd_sharp` or `rdd_fuzzy` (robust bias-corrected local linear, MSE-optimal bandwidth) → half and double bandwidth; `rdd_localrand` when few units lie near the threshold |
| An excluded instrument | instrumental variables | reduced form → first stage → 2SLS (`pf.feols("y ~ 1 | fe | d ~ z")`) |
| Few treated aggregate units | synthetic control | `synthetic_control` or `scm_diagnostics` (one treated unit), `synthdid` (a treated block) |
| Exposure built from shares and shocks | shift-share | `shift_share` → `shift_share_inference` with the identification basis (shocks or shares) fixed first; [shift-share design](../../econ-design/references/designs.md#shift-share-designs) |
| Only selection on observables | conditional independence | regression → `dml_irm` (binary) or `dml_plr` with cross-fitting → `grf` for heterogeneity |

Select the inference needed by the adopted comparison and sampling structure:

1. Cluster at the level at which treatment is assigned.
2. Few clusters, few treated clusters or very unequal cluster sizes: select an appropriate small-cluster method from wild cluster bootstrap (`wild_cluster_bootstrap`) or CR2 with Satterthwaite degrees of freedom (`club_sandwich`), using the counts of clusters and treated clusters.
3. Several outcomes testing one hypothesis: name the primary outcome in advance and report family-wise adjusted p values for the family (`romano_wolf`; `holm` for p values from separate saved results).
4. Requested event-study, pre-trend or sensitivity analysis uses its adopted contrast; ordinary estimation delivers the requested estimate and inference.

Method cards with options, checks and pitfalls: [DiD and synthetic control](../../econ-design/references/causal-models/did.md), [RD, IV, experiments and inference](../../econ-design/references/causal-models/rd-iv-experiments.md), [ML, heterogeneity and policy](../../econ-design/references/causal-models/ml-heterogeneity.md), [outcomes, bounds and sensitivity](../../econ-design/references/causal-models/outcomes-bounds-sensitivity.md), [regression foundations and engines](../../econ-design/references/causal-models/regression-engines.md). The full list of package calls is the [implementation table](implementation-engines.md).

## Step E5. Specification ladder

Run the adopted specification through the existing implementation and save the estimate, covariance and interval. Use `templates/estimate_ladder.py` when a consequential specification comparison is part of the requested result. Select additional rungs for the economic conclusion they establish; reuse saved results. Complete the requested estimate directly.

## Step E6. Diagnostics

An explicit request for diagnostics selects its null, contrast and result. Ordinary estimation or design review completes the requested estimate or derived comparison under ECONOMIST Requested work.

## Step E6b. Specification changes after the first result

The first specification, fixed in step E4 before seeing results, is the baseline and stays in the report. Repair an evident producing error from actual inputs or calculations. An explicitly requested diagnostic can inform such a repair. Record the determining change by class:

| Class | Examples | Action |
| --- | --- | --- |
| 1. Implementation or data error | wrong transformation, misaligned sample, mislabelled series, coding slip | fix and rerun automatically; record the fix |
| 2. Explicitly adopted statistical rule | lag length or selection criterion specified for this task | apply the adopted rule; record its resulting specification |
| 3. Economically motivated change | different controls, sample period, outcome definition, identification, clustering, anything that would move results toward expected signs | derive its economic reason from the fixed target; execute within the authorized scope, preserve the baseline and record the specification actually used |
| 4. Unexpected but clean result | sign or size against the prior with no error found | report and interpret; it may be the finding |

Rules:

1. Repair evident errors at their producer within the authorized scope. Keep determining changes in the existing worksheet and reuse completed work.
2. A specification is never chosen by its results. "Try X until it is significant" is replaced by a pre-specified design.
3. Keep specification-change counts and work history in worksheet section 6 (`Specification changes:`). The answer gives the requested estimate, actual specification and saved numerical uncertainty. Report determining comparisons when they establish the economic conclusion.
4. Judge unexpected results by Economic priority and their actual derivation. An unexpected sign or difference from prior estimates can be the substantive finding.

## Step E7. Interpretation

For completed estimation, fill the actual saved numeric values below. A design review delivers its strongest substantive judgment on the original question and its determining economic reason. Routine reporting arrangements stay in the worksheet.

```
Headline estimate:     <value> (SE <value>), 95% interval [<low>, <high>], <units>, <population>, <period>
Magnitude:             relative to the baseline mean, per unit of treatment, elasticity, cost per outcome
Specification changes: number after the first result, each with its class (E6b) and reason
Against predictions:   which mechanism of section 3 the estimate supports and which it rejects
Decision:              the requested estimate, or the action supported by the result
Switches when:         changed economic setting, induced response and different action; optional for estimates
```

Copy these lines into section 6 of the worksheet.
