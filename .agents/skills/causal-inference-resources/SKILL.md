---
name: causal-inference-resources
description: Use when selecting causal inference methods, finding references, comparing DiD/RDD/IV/synthetic control/panel methods, or locating causal inference libraries and tutorials from local awesome-causal-inference resources.
origin: econ-project
---

# Causal Inference Resources

Lightweight index for causal-inference references and method selection.

## Use For

- Choosing or comparing DiD, event-study, IV, RDD, synthetic control, panel,
  structural, or causal ML designs.
- Finding causal-inference courses, books, papers, libraries, or tutorials.
- Checking identification assumptions before writing or reviewing an empirical
  economics argument.

## Reference loading

Do not read the whole repository. Open exactly one starting file:

- Main index:
  `.resources/econ-ai/awesome-causal-inference/README.md`
- Academic papers:
  `.resources/econ-ai/awesome-causal-inference/src/academic-research.md`
- Books:
  `.resources/econ-ai/awesome-causal-inference/src/books.md`
- Courses:
  `.resources/econ-ai/awesome-causal-inference/src/courses.md`
- Libraries:
  `.resources/econ-ai/awesome-causal-inference/src/libraries.md`
- Tutorials or reviews:
  `.resources/econ-ai/awesome-causal-inference/src/tutorials-and-reviews.md`

## Method Triage

Match method to identification design:

- DiD/event study: parallel trends, anticipation, staggered timing, clustering.
- IV: relevance, exclusion, monotonicity, weak instruments.
- RDD: continuity, manipulation, bandwidth, functional form.
- Synthetic control: donor pool, pre-trend fit, placebo checks.
- Panel/structural work: fixed effects, equilibrium restrictions, counterfactuals.

## Boundaries

- Use `econ-writing` for prose revision after the design is chosen.
- Use `econ-research-feedback` for referee-style critique of a full draft.
- Do not treat resource-list inclusion as evidence of validity or consensus.
