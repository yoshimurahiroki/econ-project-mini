# Project integration

Use repository skills in the coding environment and SOURCE.md to identify Project attachment snapshots. Read this document only for explicitly requested distribution, synchronization, configuration, installation or state migration. Ordinary research uses the runtime and the selected specialist.

## Common core

`econ-project-mini` owns the shared source. Public and private destinations consume the registered common files and retain their own manifests, connections and project data. Account-specific plugin releases and authenticated services belong to the selected private destination. Destination receipts record the source direction and exact adopted commit for synchronized common files.

The resource source paths in [resource registry](../../registry/resources.json) define default shared instructions and tools. Entries marked sync=false remain project-owned. The synchronizer copies the same source-relative paths between repositories; it does not install deployment mappings. Each user chooses the source, destinations and paths. Origins are identified by their complete host/owner/repository path. Repositories with separate histories and different owners are supported.

Compare before applying. Supply the reviewed source HEAD and every destination HEAD. A working source also requires the comparison's `common_content_id` through `--expect-source-content`. Commit and push are separate operations.

```sh
SOURCE=/path/to/shared-template
TARGET=/path/to/research-repository

python scripts/sync_common_core.py --source "$SOURCE" --target "$TARGET"

python scripts/sync_common_core.py --source "$SOURCE" --target "$TARGET" --apply \
  --expect-source-head "$(git -C "$SOURCE" rev-parse HEAD)" \
  --expect-head github.com/example/research-repository="$(git -C "$TARGET" rev-parse HEAD)"
```

The default is a read-only comparison of the route-derived common paths. Repeat `--target` for multiple destinations or `--path` for an explicit subset. The source and destination roots must be distinct and match their Git origins and pinned HEADs. Ordinary startup, research work and environment setup do not synchronize.

A first synchronization adopts absent files. Existing files require an explicit `--claim 'HOST/OWNER/REPO:PATH=SHA256:MODE'` using the destination fingerprint reported by comparison. This claim establishes ownership of that particular path at that particular version. The three-way comparison then checks the previous receipt, current destination and new source. Uncommitted, staged and committed custom changes are protected. Resolve only the reported paths and claim their reviewed current fingerprints when choosing to replace them. Synchronization never stages files or clears the index.

Use `--migrate-receipt` to migrate a v1 receipt whose recorded source commit, blob, hash and mode can be verified. Source switching requires a separate reviewed ownership decision. Each v2 receipt records the source identity, input commit, selected hashes and modes, adoption state and destination identity. It contains no host paths or credential-bearing URLs. Project context, integration prose, research records and environment dependencies remain project-owned.

Use `--release PATH` to relinquish receipt ownership while retaining the local file and index. Released paths cannot be copied or deleted by subsequent synchronization. The explicit --release-local-configs option releases the declared LOCAL_CONFIG_PATHS; combine it with explicit --path entries when also copying common files. Remove public tracking separately with `git rm --cached -- PATH`; keep the runtime file locally and distribute its public example definition. The [configuration examples](config-templates/README.md) are managed common files; runtime MCP configurations and their generation state are local.

Deletions require `--delete PATH` with that source path absent. Moves require `--move OLD=NEW` with source OLD absent and NEW present. Existing destination paths still require their recorded baseline or a matching ownership claim. These operations stay within the explicitly selected paths.

The script checks all destinations before writing. It compares shared source inputs, repository identity and indexes at the start and final publication boundaries; immediately before each write it compares that target's content, index, repository identity and configuration. Previously written targets are checked at the final boundary. Writes use optimistic per-file atomic replacement, not a filesystem-wide transaction. It writes receipts after content, verifies the result and rolls back only its own unchanged writes on failure while retaining concurrent user changes. Exit codes are 0 for equality or successful application, 1 for comparison differences and 2 for a refused or incomplete operation.

Git `core.filemode=false` supports content updates and replay at the existing tracked mode. A mode transition requires `core.filemode=true` in a filesystem that tracks execute bits. The synchronizer refuses that transition and leaves index metadata unchanged. Run the temporary-repository checks with `python scripts/test_sync_common_core.py`.

## Standalone Project snapshots

Run from the extracted source tree; no Git repository, origin, commit, installed skills, network or model execution is needed.

```sh
python scripts/export_project.py --task econ-writing --mode compose --output /tmp/bounded-writing-new
python scripts/export_project.py --task econ-writing --mode compose \
  --condition whole_paper_abstract_introduction_or_section_architecture \
  --support econ-writing:explain --output /tmp/paper-writing-new
python scripts/export_project.py --task econ-edit --output /tmp/revision-new
python scripts/export_project.py --task econ-writing --mode translate \
  --condition example_ja_revision_translation --output /tmp/translation-new
```

`--task` accepts a specialist, operation ID, or compatibility alias. `--mode` selects a specialist mode; the default is declared in registry/operations.json. `econ-assertive` maps to writing/guidance and `econ-edit` or EDIT to writing/revise. `econ-workflow` exports the runtime boundary and asks the current task to resolve its specialist owner; `econ-handoff` exports the handoff resources for the existing result owner. Neither creates another specialist.

Without `--task` or `--skills`, the snapshot includes all five specialist bodies and their required resources. `--skills` selects specialist bodies and all their modes. Conditional resources remain inactive unless selected. `--support SKILL[:MODE]`, `--condition CONDITION` and `--references RESOURCE_ID` are repeatable. Reference selection also accepts an exact source/deployment path registered in registry/resources.json. Conditions are exact registry identifiers; misspellings fail. The operation registry defines conditions and required rule IDs; the resource registry maps each rule to its section and mandatory dependencies, and maps example IDs to language and function. Resolve their closure once per content version before rendering. Empty section selections add no body; they cannot supply a required rule. Requested headings include descendants and declared section dependencies. Missing required rules identify the rule and originating operation.

Ordinary writing includes CORE, the required PROSE sections, the chosen writing mode and exactly one selected writing profile. Profile priority is explicit `--style-profile`, adopted project preference, then default-micro. Examples are selected by language/function need. Whole-paper workflows are conditional and absent from a bounded writing snapshot. ECON_INDEX.md is generated from the selected operations; an unselected specialist index is not duplicated in the package.

Paste PROJECT_INSTRUCTIONS.txt into the Project instruction field and attach the exported files. Use a fresh directory outside the source tree. The exporter validates required files, registered links, aliases, placeholders and the 8,000-character instruction-field limit before publishing the package. Selected references resolve to flat exported aliases. Only inactive optional capabilities and examples may resolve to OPTIONAL_INPUTS.md. Activated mandatory references must resolve inside the package; a missing required rule reports its rule ID and originating operation and prevents publication. Unknown local references fail; no external-repository fallback is generated.

SOURCE.md records the logical resource ID, source path, source SHA-256, exported SHA-256, selected operations, conditions, registry hash and a content-based snapshot ID. Working source bytes are supported. Regenerate when the needed input versions change. These commands create local instruction packages; they do not update a live Project or plugin.

## Layout and generated index

The canonical source layout is skills/, runtime/, harness/, registry/, profiles/ and references/repository-policy/. The deployment paths in registry/placements.json map these to .agents/skills/, .agents/runtime/, .agents/harness/, .agents/registry/, .agents/profiles/ and repository-root policy pointers. Generate a fresh deployment package with the command below. Each selected resource is written at its declared deployment path, relative links are calculated from its destination, and client entrances are generated for that package. This creates a new package; applying it to an existing project is a separate requested operation. Export an already installed tree with --layout installed; this reads the three registries under .agents/registry/ and each declared deployment path. The exporter never guesses the layout.

```sh
python scripts/export_project.py --task econ-writing --mode revise --format deployed --output /tmp/revision-deployed-new
```

Maintenance scripts and their fixtures run from the complete source distribution. They are optional inputs in operation snapshots; explicitly selecting them fails before publishing either format, because their source-layout configuration and imports are not a standalone runtime package. The requested local team-state helper is supported separately with its declared runtime dependencies.

Both `--format flat` (the default) and `--format deployed` consume the same resolved operation and section selection. Installed input requires all three complete registries under `.agents/registry/`; an operation snapshot is not a replacement for that source registry.

Generate the repository operation index from the same registry:

```sh
python scripts/export_project.py --generate-index docs/ai/compiled_ai_skills.md
```

## Project additions and profiles

The export-project:v1 JSON block in repo_context.md supports version, writing_profile and files. Each file entry contains a repository-relative path and unique flat output filename. The persistent writing_profile can be default-micro or a repository-relative custom profile. --style-profile overrides it for this snapshot only; an absolute custom profile path is also supported. Custom inputs are hashed in SOURCE.md. Existing configuration is not rewritten.

Use econ-writing:profile (or its econ-style compatibility alias) to create or revise a profile. Creating or saving a profile does not adopt it. Switch the persistent preference only when the user requests adoption.

## Execution and handoff

Select files_calculation_external_or_resume for ordinary execution, resumption_active for saved-state reuse, delegation_active for a worker assignment, and publication_requested for an authorized publication or move. Use econ-handoff for the Handoff section and existing result owner. Select other sections only when their pending operation needs them. Existing project records remain canonical. Local state is optional; select requested_local_state_helper_operation to package its implementation when needed. An exported state.py requires --root for the actual project root. No helper starts a model or research program.

Select affected export and synchronization cases from `scripts/test_export_project.py` and `scripts/test_sync_common_core.py` using CORE. Actual generation and synchronization establish the selected package and destination behavior; reuse those results. The existing fixtures cover ownership, dirty-source, staged-index, rollback and execute-mode behavior.

## 0.12.0 changes and measured evaluation

Version 0.12.0 selects execution structure at the actual dependency. Settled input/output contracts use the existing procedure; prerequisites remain sequential; independent reads and isolated writes can run concurrently; specialist delegation accounts for briefing, coordination and integration. Shared-resource ownership includes session keys, browser tabs, transactions and remote targets. Returns retain their assignment/tool-call and input-version identity. The existing five specialist owners, operation registry, instruction authority and outcome completion rules remain in force.

Code work follows the real entry point to the owning definition, complete current body, relevant callers and working implementation. An available language server resolves ambiguous symbols or cross-file changes; known local changes use the existing patch path. General code exploration is owned by EXECUTION and referenced by econ-data. Repeated failures are compared by effective input, code, environment and returned error. Complete operation output is retained before a shortened display is used, and required original text is restored from its source.

The existing state helper now supports `find QUERY`, with exact parent/owner/recorded-status filters and snapshot-bound pagination. Candidates point to the original request, rules, adopted decisions, results and recorded failures. Selected `show` and existing resume/version checks establish applicability. Search is read-only and adds no database, transcript collector, embedding service or memory authority. TEAM and the existing helper/resumption routes load this capability through the resource registry.

The baseline is mini `bc96f1890dc06864091985129ed28f8eccba5506` and full `2cceb24a351b526a86fabe6f47d25aa8cb94a58c`, version 0.11.0. Same-input measurements used actual existing entry points:

| Operation and retained result | Before | After |
| --- | --- | --- |
| Locate the specified parent's saved PPML case in a 50-task synthetic store, then restore its full task record | Whole-store `show`: 565,059 UTF-8 bytes, one CLI invocation | `find` plus selected `show`: 11,927 bytes, two invocations; complete selected record, outputs and governing context identical |
| Locate the same parent's historical packaging failure and restore its full record | 565,059 bytes | 23,483 bytes; original history and references retained; store bytes unchanged |
| Generate the full distribution from identical 0.11 inputs | 60.695 seconds elapsed; 60.639 process CPU seconds | 6.499 seconds elapsed; 6.458 process CPU seconds |
| Interruption and resumption through the existing 33-call lifecycle | Original context restored; four lossy context updates and premature completion rejected | Same results; one analysis computation, no unnecessary child reassessment, identical analysis and recommendation hashes |

The distribution optimization validates each unchanged resource body, locator and selected scope once within its immutable verification invocation. Every operation retains its required-rule and selection coverage; each later snapshot rereads its bytes. Publication ownership, input-change detection, rollback, links, syntax and control-character checks remain active. Across the paired 550-file generated trees, 537 files were byte-identical; the other 13 were the two changed implementation modules, their bundled copies and corresponding integrity manifests. All generated rule bodies were identical. An initial separate timing pair was 60.152 versus 6.241 seconds. These are local generator measurements, not hosted-CI or model-token measurements.

Existing state tests exercised retained authority, holds, dependency versions and completion, with three added search cases. The existing exporter suite passed 52 cases, including shared-resource section validation, later-snapshot changes, malformed control text and omitted selections. The changed local-helper export is exercised in flat and deployed layouts using the actual `find` command and its packaged body. The 33-call lifecycle checked initial, intermediate, post-compaction-proposal, resumed and final records. No unseen-paper content or result was used for development or evaluation.

Two independent fresh agents also executed the same code, source-inspection and data-analysis assignment using their respective rule versions. The calibrated two-product logit project initially mixed counterfactual prices with stored baseline shares. Both agents read the installed PyBLP 1.3.0 implementation, repaired the owning profit function, invalidated its affected cache and saved the required JSON and Japanese decision memo. Both obtained baseline profit 1.1978837249168965, common-owner profit 1.3748225281836233 and net gain 0.07693880326672672 at transaction cost 0.1, selecting merger. An authorized continuation changed only transaction cost to 0.2: both retained the identical saved model result and run counter at two, regenerated the artifacts, obtained net gain -0.02306119673327328 and selected separate ownership. Original model parameters, population, objective and unused method were preserved. This case establishes completed repair, correct package use and continuation in both versions; it does not establish a general model-quality improvement rate.

Twenty OSS implementations and the 21 design-pattern applicability discussions were compared with these existing owners; detailed public provenance is retained in the root notices. The release adds no external runtime dependency, model service, permanent agent, hook, state store or standalone evaluation framework. Existing environment locks, separate quality environment, CI selection and official synchronization/publication paths are reused.

## 0.11.0 changes and measured evaluation

Version 0.11.0 connects issue priority to the downstream work invalidated by a wrong premise. The existing decision, design, execution and delegation owners identify the determining population, mechanism, model or interface; obtain the discriminating observation or smallest real calculation; and carry the result into dependent work. Unaffected completed work remains reusable. Required instructions, deliverables and verification retain their authority and coverage. No separate agent, state system, checker, estimator, wrapper or runtime dependency was added.

The comparison baseline is mini `3975116892cc443a71f7bc4c3244f52e294da45b` and full `43c8a466300df1e0519881aaec0afcf91f8d0f49`, both version 0.10.0. The following comparisons used the same inputs and actual entry points before and after the change.

| Observed operation | 0.10.0 | 0.11.0 |
| --- | --- | --- |
| New data pipeline or code-change export | Omitted the existing execution entry/dependency and output/failure bodies | Includes both bodies in flat and deployed exports |
| Compound mini CI change | Four pytest processes for four affected suites | One pytest process retains those suites and includes the existing configuration suite |
| Corresponding full CI selection | Selected a mini-only test absent from the full repository; exit 1 | Selects the full repository's existing suites; exit 0 |
| Two routine `make sync` calls | Ten privileged filesystem calls and two installer calls | Zero privileged calls and the same two installer calls |
| Kernel registration in a relocated checkout | Failed at a fixed `/workspaces` path | Resolves the project from the script and reaches Python/R registration |

The CI and environment comparisons executed their real shell entry points with controlled external executables that recorded operations and injected failures. Installer failure, missing R kernel and pytest exit 19 remain failures. Container-volume ownership is established in the existing initialization script; routine synchronization runs as the current user. Existing lockfiles, dependency declarations, cache volumes, pre-commit controls and instruction entrances are retained. The measurements establish operation selection and failure propagation; container builds, dependency downloads and hosted-CI elapsed time were outside this comparison.

The prose integration changes content selection before word editing: retain the proposition, evidence, causal relationship, quantity and action needed for the reader's judgment, and remove content serving rhetorical self-protection. Eight existing semantic criteria had described the defect in imperative form, including instructions to add concessions or replace a concrete request with generalities. They now direct the removal or reconstruction of that defect. The 142 lexical records, all 22 semantic IDs and names, required actions, instruction precedence and prohibition on rhetorical exceptions are unchanged. Existing writing modes and integrated review own this work.

Direct specialist-package calculations exercised consequential method choices using declared synthetic models:

| Decision quantity | Incompatible calculation | Matching calculation and result |
| --- | --- | --- |
| Two-product merger, homogeneous logit, marginal costs 1, transaction cost 0.1 | Fixed-demand price approximation: incremental profit −0.4397878760; pricing-equation residual 0.2290854151 | PyBLP 1.3.0 equilibrium: incremental profit +0.0769388033; residual zero at returned precision |
| Profit at the new equilibrium | New prices with default baseline shares: 1.7791524025 | Explicit new prices and recomputed shares: 1.3748225282 |
| Expanding participation beyond the instrument's observed margin | Treat historical LATE 1 on (0.2, 0.4] as the new-margin effect | Two compatible response curves imply net policy values +0.2 and −1 on (0.4, 0.8]; the determining unknown is the new margin's mean effect, with boundary 0.5 |
| Finite tax change 10 to 30, demand 100 minus tax and external damage 15 per unit | Extend the initial welfare derivative across the full change: +100 | Integrate the derivative along the path: −100, comprising external benefit 300 and extra deadweight loss 400; tax transfers cancel |

The merger uses two separate firms at baseline, one owner in the counterfactual and market size one. These comparisons establish calculation behavior under the stated models. They do not estimate an empirical market effect or a model-level behavioral improvement rate. Design and data instructions now trace the economic quantity through identifying support, package arguments, returned arrays and the action threshold before extending dependent analysis.

Separate fresh agents used the same synthetic board-decision task and saved their initial and updated Japanese memos. Both versions selected B at total incremental profits A = 12 and B = 21 million yen, retained the 120-million-yen capital budget and rejected the infeasible joint project. Both calculated the switching boundary at an existing-product contribution of −32 million yen. When the authorized input changed from −41 to −27, both updated the saved memo to select A at profit 26 versus 21, with an 80-million-yen initial investment and the responsible manager's next procurement-specification action. Existing population, horizon and cost definitions remained intact. This comparison confirms the observed decisions and completed artifacts in both versions; no general behavior-improvement rate is inferred.

The two corpus indexes assigned a consulted paper to different partitions. The new rule and example additions depending on that paper were withdrawn. Existing adopted analysis instructions remain intact. No unseen-paper evaluation was run or used for this release.

The existing state mechanism was also exercised on the same 33-call sequence in both versions. Both rejected all four proposed omissions of the original request, active instructions, adopted decisions and objective; rejected parent completion without the final requested file; resumed with original context; and completed both artifacts. Initial, middle, post-compaction-proposal, resumed and final observations retained parent and child context. Each version computed the analysis once and required zero unnecessary child reassessments. The analysis and recommendation hashes match the 0.10.0 comparison below. This run confirms preservation of the existing resumption behavior.

Nine existing configuration cases passed with three added regression methods covering the changed entry points. Two existing exporter methods exercised the two changed conditions in both formats and all thirteen operations across five owners. Two existing equity cases executed demand recovery/ownership equilibrium and the steady-value/share-unit/holding-return bridge. Validation reuses these results and the actual generated packages. Public operational instructions contain generalized original procedures; development provenance remains in the root notices file.

## 0.10.0 changes and measured evaluation

Version 0.10.0 connects evidence-derived parent claims, reader-dependent content selection, project decomposition, delegated results and resumption through the existing owners. The common writing path now distinguishes the premises needed for an inference, derives an informative parent proposition from its supporting relationships, and returns a missing comparison to its analysis owner. Proposals, research explanations, progress reviews, discussions and oral explanations select information by the recipient's actual judgment. Multi-stage work connects the current answer, supporting propositions, producing operations and accumulated outputs. Fixed requirements retain their original authority; delegated analytical choices can change on evidence within their adopted switching condition.

The state helper now keeps governing context revisions beside its existing requirement history. Removing or replacing the original request, active rules, fixed decisions or governing objective needs the already-given user instruction bound to the old and new context. A delegated decision uses a new version and saved evidence for the unchanged switching condition. This is retained declaration and content identity, not signed authentication or automatic semantic validation. Progress updates, identical rebinding and additive references remain usable. No separate framework, management ledger, production agent or runtime dependency was added.

The comparison baseline is `f35e8d13d6f9fe523539c51636572a46deb89752` (0.9.0). The same real CLI sequence registered the original sources, calculated a child result, bound the parent's consumed output, interrupted the task, proposed four lossy context updates, resumed and completed both requested files.

| Observation | 0.9.0 | 0.10.0 |
| --- | --- | --- |
| Updates deleting the request, active rules, adopted decisions or objective | Accepted 4/4 | Rejected 4/4 |
| Resume with original context after those proposals | Exit 2 | Exit 0 |
| Parent and child context after proposals and at resume | Replaced | Original retained |
| Unnecessary re-completion of the child after restoration | 1 | 0 |
| Parent completion without its final requested file | Rejected | Rejected |
| Actual analysis computations | 1 | 1 |
| Final analysis and recommendation | Both completed | Both completed; identical output hashes |

The changed implementation retained the original context at initial, middle, post-proposal, resumed and final observations. Analysis SHA-256 was `aece227ae60b5e60f83abc86871cf7305a462ee78f966af4ea9641781792a817`; recommendation SHA-256 was `ead8d573fe1ed141d14404420cf3e7a5a40a0801189ede8fee415a64c9cdfdba` in both versions. The sequence used 34 versus 33 CLI calls and took 2.203 versus 2.101 seconds in one local run. These timings are descriptive, not evidence of a general speed improvement. The sequence reproduces a compaction-boundary failure; it is not an hours-long model-success benchmark.

A second actual distribution comparison found that the old `resumption_active` export omitted the already existing Governing context section. Registering that section and its dependencies now includes its original-source restoration and revision instructions in both flat and deployed exports. The standalone flat export still contains ten files. Delegation also selects the existing Return and integration body. This repairs access to the rules rather than adding another rule owner.

Separate fresh agents executed the same synthetic business-analysis task with the old and new implementations. Initial evidence left onboarding channel shifts unknown; both computed the action-switch boundary at 90 customers without inventing a measurement. Reconciled evidence then supplied 105 shifts. Both selected discount: 60 genuinely new customers and net contribution 40 thousand yen, against repair's 55 customers and 10 thousand yen. Both retained the 1,000-person denominator, one-year horizon, 120-thousand-yen budget and all four alternatives, with the 180-thousand-yen combined option infeasible. Fresh workers then resumed from a secondary handoff favoring the wrong gross-uptake comparison. Both recovered the original contract and saved evidence, retained discount, and delivered executable scripts, CSVs and Japanese memos (260 and 313 characters). Final CSVs and memos matched each implementation's completed phase-two outputs byte-for-byte. The changed implementation retained its initial context and its evidence-bound delegated-decision revision in the existing state helper. This development task demonstrates preserved decisions and usable artifacts in both versions; it does not establish a general model-quality improvement. Restart used fresh workers, not an observed host compaction.

The existing state suite passed all 60 tests, including three added regressions for consequential context loss, authority/evidence-bound revisions and intact resumption. Three selected exporter tests and the existing equity suite ran 19 cases: 15 passed and four optional-dependency equity cases were skipped. Source and deployed instruction links have zero failures. No unseen paper-corpus contents or evaluation results were used to create the rules; the existing discovery/counterexample/unseen separation is preserved.

## 0.9.0 changes and measured evaluation

Version 0.9.0 connects the central economic issue and obstacle to the next comparison, calculation or execution step through the existing runtime and specialist owners. Source assessment distinguishes an organization's claim from its underlying observations, and method selection preserves the adopted estimand and requires a matching specialist implementation. Completion uses returned execution status and the requested output. Existing writing, valuation, export and synchronization responsibilities remain in place.

The comparison baseline is `426c54731a017aaedb7b5cbf5d008431b2b7f55c`. The old and new state mechanisms received the same six inputs. The old mechanism accepted all six: a success string without completion evidence, exit status 1, a running operation, `isError`, a result for another target, and a successful exit status 0. The new mechanism rejected the first five and accepted the successful exit status 0. This comparison establishes the changed acceptance behavior of the state mechanism.

Separate fresh agents applied the old and new rules to the same four development tasks:

| Task | Observed outcome in both versions | Additional observed difference |
| --- | --- | --- |
| Policy choice | Reject the intervention with aggregate net benefit of minus JPY 550,000. | None in the selected action. |
| Price competition | Choose the dominant price of 10, yielding profit of 200. | None in the selected action. |
| Estimator and package choice | Preserve the adopted fixed-effects OLS specification for the count outcome and reject an unsupported DRDID argument. | The old answer leaned toward custom implementation for the auxiliary estimate; the new answer prioritized a specialist implementation matching the doubly robust score and inference. |
| Independent product judgment | Choose B; retain B under pressure without new evidence; switch to A when new measurements change the comparison. | None in the selected actions. |

Both versions answered all four development tasks correctly. The observed package-selection difference concerns the proposed next implementation step; it does not establish that the auxiliary estimator was executed. These single-run tasks do not measure a general improvement in model ability. The existing 100-paper corpus's unseen partition was not used. Two existing stock-valuation tests also passed.

A separate numerical execution directly used the installed scikit-learn 1.8.0 `PoissonRegressor(alpha=0, solver='newton-cholesky', tol=1e-12)` and `LinearRegression`, adding no dependency. The eight-observation nonnegative count sample retained both zeros and had group means of 1.5 and 3. PPML returned a group coefficient of `0.6931471805599455` (absolute difference from log 2: `2.22e-16`), a mean ratio of `2.0000000000000004` and a score residual of `4.44e-16` after five iterations. OLS returned the level difference of 1.5. The fits took 0.134 seconds in total, and the saved sample, fitted values and result were reread. This run verifies point estimates; it did not perform fixed-effects absorption, cluster-robust inference or causal identification.

## Distribution and settings contract

Read this section only for requested export, installation, synchronization or configuration work. The [operation registry](../../registry/operations.json) defines modes and conditional rule selection, the [resource registry](../../registry/resources.json) defines logical resource IDs and rule dependencies, and the [placement registry](../../registry/placements.json) defines physical locations and export aliases. Use the registered resource IDs and the selected layout when exporting or synchronizing. Read the relevant command section and its supported options. Compare common inputs at batch boundaries and each destination immediately before writing; do not reread every unchanged input for each target.

For an export, select CORE, the final operation and its activated support/resources. Include only sections needed by those operations. Short prose does not activate whole-paper instructions. Resolve every active mandatory reference inside a standalone package. An omitted optional capability becomes an additional input if later needed; do not turn it into an automatic remote-repository fetch. Resolve resource paths through the declared placement and export aliases. Check required files, references, unique output names and requested size limits before producing the complete package in a new destination.

The configuration interface defaults to a diff, changes only explicitly selected clients or adopted project targets, and rejects unknown arguments or incompatible modes before writing. Read every selected destination and required input, then assemble all intended changes. Include devcontainer only when selected. Resolve relative paths from the command's declared project root.

For each generated setting, compare the previous generated content, current content and proposed content. Update a setting only while its current value matches the previous generated value. Preserve manual changes and mark the item manually owned. Recheck content immediately before applying and preserve detected concurrent changes. The helper uses per-file atomic replacement with optimistic rereads. Coordinate other writers across the final read-to-replace interval. For a caught multi-file write failure, roll back only content still matching this operation's writes. A process crash requires inspection of the actual destinations before resumption. Legacy name-only ownership records do not establish content ownership; preserve those entries until their ownership is resolved.

Reference secrets through existing environment or approved storage rather than embedding them. Required configuration or installation failures must propagate as failures with the affected targets. Preserve successful work, diagnose failed items and retry only the affected operation. Report the returned statuses; an instruction to perform an operation is not a successful operation result.


## State migration

Use explicit capacity, depth or attempt limits only when the user or runtime supplies them. Migration preserves saved outputs, bound check receipts, usage, holds and limit provenance. A legacy task lacking declared deliverables retains an unresolved completion contract; recover the request and use set-contract rather than infer requirements from whatever output exists. Previously completed tasks with an unresolved contract become blocked while their results remain saved. Legacy permission/user-hold reasons without an identifier receive an identified legacy hold. Perform missing required operations against preserved current results; migration does not rerun calculations.


An old evaluating state maps to running; interrupted maps to blocked with blocked_reason=interrupted. Schema-v4 migration preserves outputs, check receipts, authority, holds, attempt counts and usage. Where recorded consumed inputs identify one parent output unambiguously, migrate to that explicit consumes edge. Otherwise retain the legacy dependency set as a compatibility group until the next relevant operation establishes its input contract; never erase it or guess a narrower dependency. Migration alone does not invalidate numerical results or rerun completed stages.
