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

### Native configuration dependency and continuation

`core.task-entry` requires `team.native-model-roles`, so the ordinary operation retains Sol's authority and the bounded child contracts. The existing `requested_distribution_configuration_or_installation` condition additionally selects the three `policy-codex-agent-*.all` rules and `config-template-codex-example-toml.all`. Their registered source files are public templates; deployment maps child files to `.codex/agents/` and retains the primary template in the configuration documentation. The [configuration commands](config-templates/README.md#native-sol-terra-luna-and-astra) produce flat aliases or deployed paths through this same closure.

The standalone fields follow the pinned [Codex role parser](https://github.com/openai/codex/blob/67f0994b532b8740f14b5b738af7b7b2a915b1d6/codex-rs/agent-roles/src/agent_role_config.rs). The pinned [child configuration implementation](https://github.com/openai/codex/blob/67f0994b532b8740f14b5b738af7b7b2a915b1d6/codex-rs/core/src/agent/child_config.rs) supplies model/effort precedence and parent permission, provider and MCP inheritance. The exporter preserves executable/data-resource bytes; each `SOURCE.md` records the source and exported SHA-256 alongside its logical resource and physical output path. This separates the always-required decision contract from the explicitly selected configuration artifact.

The installed-layout continuation consumes the same deployed resource mappings and complete registry versions. It regenerates only the requested exports, compares native TOML metadata and bytes with the selected source, and retains the completed first exports. The primary template's provider/login settings, the three requested child models and `xhigh`, and Sol's fixed research authority carry through both layouts.

A repository can retain canonical source and a deployed `.agents` tree together. The source policy uses `quality/policy_manifest.json`; the deployed policy uses its registered `.agents/quality/policy_manifest.json` with repository-root deployment paths. Discovery matches the actual policy module against the installed placement before treating the nested registry as a source root. The focused coexistence regression reproduces the former doubled `.agents/.agents` lookup, verifies both adopted manifests and proves that a changed deployed CORE leaves the source manifest valid while invalidating the deployed one. Deployment adoption preserves canonical root documents and binds the actual adopted bytes through the deployed manifest and source snapshot.

## 0.13.0 native model roles and measured evaluation

Version 0.13.0 assigns Sol the permanent research and final decision authority. Terra implements bounded specifications; Luna processes routine source and format batches; Astra receives only the consequential exceptionally hard core remaining after Sol's substantive attempts and cause-specific repair. CORE loads TEAM's role section for every operation. The existing registry, state outputs, Codex hook instruction packets, exporter and synchronization path distribute the same contract. The five economics specialist owners and fixed analysis specifications retain their existing responsibilities.

The native setup uses the existing `setup_ide_mcp.sh --codex-team --client codex` path and public role templates. Its explicit write selects `gpt-6.1-sol`, `xhigh`, native OpenAI provider and ChatGPT login and installs the three standalone child TOMLs. Project scope is the default; `--scope user` selects `CODEX_HOME`, or `~/.codex` when that variable is absent. Both scopes use the same preview, write, check, ownership and concurrent-edit path. Existing capacity, permissions, MCP declarations and unrelated settings are preserved. The [configuration instructions](config-templates/README.md#native-sol-terra-luna-and-astra) supply the commands. Team-only setup ignores environment-driven MCP generation; the ordinary setup command owns that separate operation.

### Native environments and observed execution

The official references were read on 2026-11-01 JST (2026-10-31 UTC): [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [configuration](https://learn.chatgpt.com/docs/config-file/config-reference), [models](https://learn.chatgpt.com/docs/models), [Work and Codex](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex), [Astra usage](https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex) and [agent orchestration](https://developers.openai.com/api/docs/guides/agents/orchestration). The source investigation pins OpenAI Codex at `67f0994b532b8740f14b5b738af7b7b2a915b1d6`.

| Environment | Actual configuration and route |
| --- | --- |
| Codex CLI | User `CODEX_HOME` or `~/.codex` contains `config.toml` and `agents/`; trusted project `.codex/config.toml` and `.codex/agents/`; native ChatGPT login. Terra requires CLI 0.159.0 or later. |
| Codex IDE extension | Local native configuration and authentication, constrained by its installed version and actual model catalog. |
| Codex desktop | Native client settings and local project roles; its hosted Work surface uses the hosted launch schema. |
| ChatGPT Work | Composer-selected primary and actual native child model/effort arguments. A fixed primary can transport actions for a separately launched Sol manager. |
| ChatGPT Chat | Its own model selection and message accounting; the Work-specific Sol, Terra and Luna model choices belong to Work. |
| API | Separate billing and credentials. This implementation uses native Work and ChatGPT-authenticated Codex. |

The connected CLI reported version `0.164.0` and `Logged in using ChatGPT`. Its catalog advertises `xhigh` for all four requested IDs. Native Work accepted explicit fresh-context Sol, Terra and Luna launches and returned task identities. The current host wrapper returned no observed model, effort, token or allowance fields. Its selected root remained Astra; the explicitly launched Sol manager made the substantive decisions and the root handled transport and publication. Astra specialist launches: zero.

Custom roles supply their own `developer_instructions`, replacing the parent's same-named configuration field. Each role therefore reads the governing entry, CORE, PROSE, TEAM, registry, selected skill and activated bodies and returns further assignment needs to Sol. The pinned [child configuration](https://github.com/openai/codex/blob/67f0994b532b8740f14b5b738af7b7b2a915b1d6/codex-rs/core/src/agent/child_config.rs) applies role model and effort after explicit spawn settings and restores the parent's runtime permissions and working directory. The pinned [configuration type](https://github.com/openai/codex/blob/67f0994b532b8740f14b5b738af7b7b2a915b1d6/codex-rs/config/src/config_toml.rs) marks `max_depth` as V1-only and ignored in V2. Sol's launch ownership and one writer per shared file govern the selected workflow; host permissions supply its actual execution boundary.

Native CLI, IDE and desktop share the local configuration. Work exposes its own launch schema and tool permissions. In this session, model overrides require `fork_turns="none"`; the brief supplies the original purpose, fixed target, applicable rules, inputs, allowed judgments, write scope and completion condition. The configured roles retain OpenAI's native provider and `forced_login_method="chatgpt"`. ChatGPT authentication uses the subscription allowance; API-key authentication uses separate API billing. Work and Codex share the allowance reported in Settings Usage, whose remaining amount and reset state are the applicable account observations. Returned token counts provide their recorded token measure; allowance accounting comes from the allowance source.

Codex's `account/usage/read` protocol supplies thread groups with model, effort, input/cache/output/total tokens and estimated credits when available; `account/rateLimits/read` supplies allowance state separately. The local app-server read failed before initialization with a read-only filesystem response, and the documented daemon read returned an `Operation not permitted` response. These operations produced no usage observation. Requested models, accepted task identities and elapsed clocks are retained as their own evidence.

### Pinned implementation investigation

Each row records actual inspected source or an explicitly identified workflow source, its pinned revision and the determining application. Provider SDK examples and source test fixtures were read; this release installs the native role configuration and existing Python implementation. The source investigation ran through public GitHub reads without paid inference APIs.

| Repository and pinned source | Inspected mechanism | Application and evaluation evidence |
| --- | --- | --- |
| [openai/codex](https://github.com/openai/codex/blob/67f0994b532b8740f14b5b738af7b7b2a915b1d6/codex-rs/agent-roles/src/agent_role_config.rs) (`67f0994b532b`) | Standalone role parsing, child model precedence, inherited provider/permissions/MCP and native telemetry schema. | Use supported `name`, `description`, `developer_instructions`, `model` and `model_reasoning_effort`; distinguish request from observed launch data. |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python/blob/e355d69152d4f4730dfb03b63dbce53e8d9f5d8c/src/agents/handoffs/__init__.py) (`e355d69152d4`) | Scoped handoff input and settings overlay. | Keep the complete bounded brief and supported settings. Usage tests use scripted counts; the optional Codex extension launches the CLI. |
| [openai/openai-agents-js](https://github.com/openai/openai-agents-js/blob/9b33d73a3ad696f0c43689d1428e901bfdc37fa0/packages/agents-core/src/usage.ts) (`9b33d73a3ad6`) | Typed reasoning settings, input filtering and returned usage. | Record supplied runtime fields. Runner usage tests use synthetic counts; the sandbox example requests an API key. |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph/blob/e5c961d7fbe7ca6fdd4c94c84d90511372514d55/libs/langgraph/langgraph/pregel/_retry.py) (`e5c961d7fbe7`) | Selective retry clears the internal task write buffer. | Repair the failed unit and inspect external state. Retry tests distinguish matching exceptions. |
| [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents/blob/e21ce33d4486899069dda55254e6ec56e874a854/libs/deepagents/deepagents/middleware/subagents.py) (`e21ce33d4486`) | Isolated child brief, excluded private state and changed-state return. | Give task-specific sources and one return contract. Its named-task tests assess SDK integration; eval setup requests provider credentials. |
| [microsoft/agent-framework](https://github.com/microsoft/agent-framework/blob/b7884ad88eb85c27b2a7bf40c0e15948e7ccc28d/python/packages/core/agent_framework/_workflows/_state.py) (`b7884ad88eb8`) | Staged writes, checkpoint lineage and last-writer-wins shared keys. | Use one writer and retain completed boundaries. Usage middleware reads returned counts; the evaluation sample uses Azure credentials. |
| [google/adk-python](https://github.com/google/adk-python/blob/8cd3b12c8a5d658c5e0d3ea0731d8be34a092a4a/src/google/adk/workflow/_parallel_worker.py) (`8cd3b12c8a5d`) | Branch-scoped history and per-item parallel recovery. | Resume the affected item and retain siblings. Usage tests preserve the latest returned report and retain absence; efficiency evaluators report supplied counts. |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI/blob/97bbfb64811775a965304bda45c8ec0e8e4ef3a2/lib/crewai/src/crewai/tools/agent_tools/delegate_work_tool.py) (`97bbfb648117`) | Explicit task, context and coworker delegation fields. | Bind assignment to its return. Usage parity tests use fixed fixtures; provider tests explicitly exercise API-key handling. |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai/blob/2a89126b7a968ae7664348dc055717e0e2bb61f9/pydantic_ai_slim/pydantic_ai/usage.py) (`2a89126b7a96`) | Fresh named delegates, per-request model settings, conversation-store lineage and returned usage aggregation. | Preserve per-call model and observed resources; source usage limits and evaluation reports use the SDK's actual run objects. |
| [agno-agi/agno](https://github.com/agno-agi/agno/blob/a9ea2b48b4d9bc5cfdea10d39ab5b8de66343a5f/libs/agno/agno/agents/codex/agent.py) (`a9ea2b48b4d9`) | Native Codex app-server adapter, explicit reasoning effort, retained ChatGPT login and persisted thread identity; team dependencies and measured evaluators. | Confirms the native host's login, effort and thread controls. Use Codex's own implementation and the existing state owner. |
| [wshobson/agents](https://github.com/wshobson/agents/blob/7e2fb559cf4b824b27f1fec49fe88f7511066d26/plugins/agent-teams/agents/team-lead.md) (`7e2fb559cf4b`) | Team-lead and delegation workflow with exclusive file ownership. | Retain the existing one-writer rule. Optimization prompts describe metrics; inspected paths supply workflow text. |
| [affaan-m/ECC](https://github.com/affaan-m/ECC/blob/b38be6a7f6350964d59328b52f0624e1d1d552d1/skills/agent-eval/SKILL.md) (`b38be6a7f635`) | Owned work cards, integration evidence and task-commit evaluation workflow. | Pin inputs and compare completed outputs, elapsed time and exposed usage. Metrics and trial counts are workflow instructions. |
| [obra/superpowers](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/SKILL.md) (`2ce8aa15d05b`) | Fresh task briefs, role capability selection and ledger/Git recovery. | Retain original sources and resume unresolved work. Select reviews through the existing CORE/CONTROL contract. |
| [microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer/blob/e428fc91b0f8ffecb5a596d56b14fe2f1485a5f9/tokeneconomizer/plugin/accounting.py) (`e428fc91b0f8`) | CLI side calls and cache-aware ledger/pricing/accounting code. | Count actual mechanism overhead and separate credits from allowance. Published README percentages remain that repository's reported benchmark. |
| [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents/blob/d20c728368bf9c189d6d7aab704744decb6ec0cc/packages/create-12-factor-agent/template/src/agent.ts) (`d20c728368bf`) | Serialized thread state, small bounded loops and application-owned control flow. | Reuse the existing state and native host. The inspected starter loop supplies control flow without usage/evaluation counters. |
| [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli/blob/6814e00d6b148c3a1d57244d5d7040f7c541009d/evals/subagents.eval.ts) (`6814e00d6b14`) | Agent registry, model-scoped config and behavioral delegation evaluations. | Keep host model precedence and role semantics separate. Source evals cover relevant delegation, trivial edits and sandbox recovery. |
| [Aider-AI/aider](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/architect_coder.py) (`5dc9490bb35f`) | Separate architect/editor prompts, restored chat history and benchmark aggregation of pass rate, elapsed time, tokens and context exhaustion. | Keep design and bounded implementation distinct and compare completed artifacts with observed resources through the current host. |

The additional Claude Code public-source check pinned `80c6959d28c4c30ecd14fc1cdf172f19d9adad81` and read its [settings example](https://github.com/anthropics/claude-code/blob/80c6959d28c4c30ecd14fc1cdf172f19d9adad81/examples/settings/settings-hipaa.json) and README. Those paths expose configuration examples and a usage-data disclosure. Gemini CLI supplies the additional inspected delegation implementation.

The resumed source pass reused saved findings at matching commits and read additional code for settings, delegation, context, isolation, resumption, evaluation and host fit. It advanced Pydantic AI to the pinned revision above. [ECC's native configuration](https://github.com/affaan-m/ECC/blob/b38be6a7f6350964d59328b52f0624e1d1d552d1/.codex/config.toml) and Agno's adapter supplied direct Codex examples. [TokenEconomizer's Codex hooks](https://github.com/microsoft/TokenEconomizer/blob/e428fc91b0f8ffecb5a596d56b14fe2f1485a5f9/plugin/hooks/codex-hooks.json) show lifecycle integration whose judge invokes the configured CLI and consumes its account resources. CrewAI's `Crew.test` call site was inspected; its internal evaluator implementation remains outside the inspected source. The implementation reuses native roles, the existing state, deterministic checks and the current hook packet.

### Resumed native execution

The resumed Work session accepted `/root/sol_manager` for the requested `gpt-6.1-sol` manager, `/root/sol_manager/terra_source_research` for requested `gpt-6.1-terra`, and `/root/sol_manager/luna_source_research` for requested `gpt-6-luna`, each at requested `xhigh` with fresh context. Child launch returns contained `task_name`; observed model, effort, token and allowance values remain absent. Sol owned the source-adoption, method, assignment and integration decisions. Terra returned the seven-repository implementation survey and the bounded project/user installer change; Luna returned the nine-repository routine source survey. The primary host performed authorized repository and plugin transport. Astra specialist launches: zero.

Terra's returned implementation clock is 2026-10-31 15:30:47–15:33:11 UTC. Its existing configuration suite passed 23 cases using temporary HOME and CODEX_HOME destinations, covering both scopes, preserved settings and capacity, edited-role conflicts, ownership reuse across projects and supported write boundaries. This clock describes the returned bounded implementation; the paired measurements below retain their original producing runs and input identities.

### Same-input native pilot

The shared packet fixes three adopted cohorts (2015/2017/2019; baseline resident counts 1,200/800/1,000), a never-treated cohort of 1,100, 2012–2021 periods, a simultaneous administrative-recording change, independent survey take-up and the stated conditional parallel-trend/no-anticipation/overlap conditions. Sol selects survey-based group-time ATT and fixed resident weights; Luna extracts the cohort facts.

The economic input fixes alpha `-0.8`, two four-product conditional markets U/V with masses 1,200/800, baseline prices `[5.1,4.8,5.3,5.0,6.1,5.7,6.3,5.9]`, shares `[.30,.25,.20,.25,.35,.20,.25,.20]` and owners A/B/C/D in each market. A and B merge; C and D remain independent. Both conditions use existing `equity_io.py:conditional_logit`, recover baseline costs and solve every owner's counterfactual response. The copied faulty profit function uses baseline shares; the repair uses the candidate shares with the candidate prices. The two transaction costs are 50 and 500.

The routine input contains 600 JSON rows: for row `i=0..599`, entity `i%120`, vintage `i//120`, publication year `2020+vintage`, eligibility `entity%7!=0`, amount `(entity*17+vintage*13)%101` and suppressed status when `(entity+vintage)%11==0`. The procedure selects the latest vintage at cutoff 2023, retains eligible observed records and classifies amount at least 50 as high. The bounded continuation uses the existing `state.py` CLI to register calculation/memo outputs, complete, requeue only the changed-cost memo, complete again, and retrieve the saved task. The fresh solo condition makes 14 actual CLI calls and the team condition 12; every call returns zero. Each condition performs one equilibrium calculation and preserves its saved hash across continuation.

| Task class | Fresh solo Sol | Sol with Terra and Luna | Completion comparison |
| --- | --- | --- | --- |
| Research design | Survey-based doubly robust cohort-time ATT, never-treated controls and fixed resident weights. | Sol selects survey cohort-time ATT and the same fixed target; Luna extracts cohort facts. | Both preserve the resident target, supplied conditions and take-up/recording comparison. |
| Economic calculation | Baseline A+B profit 1,931.3186813186812; counterfactual 2,129.070670747385. | Same quantities. | All eight prices, shares and costs agree within 1e-10; maximum residual 4.44e-16. |
| Code search and repair | Replaces stale baseline shares in the owning profit formula. | Terra implements the fixed candidate-share formula. | Repaired and direct candidate profits agree exactly in both runs. |
| Routine batch | 92 selected IDs; total 4,545; mean 49.40217391304348; high/low 46/46. | Luna returns exactly the same IDs and summaries. | Cutoff, eligibility and observed/suppressed treatment match. |
| Bounded continuation | 14 state CLI calls, completed saved task and one retained calculation. | 12 state CLI calls with the same completed output contract. | Memo-only continuation preserves each condition's calculation bytes and run count. |

Sol's decisions are merger at cost 50 (net gain 147.75198942870384) and separate ownership at cost 500 (net gain -302.24801057129616).

| Timed condition | Elapsed seconds | Observed scope |
| --- | ---: | --- |
| Fresh solo Sol, requested `gpt-6.1-sol`/`xhigh` | 305.558127039 | Fresh-context launch, required reading, all five task classes, integrated checks and actual completion timestamp. |
| Sol manager with Terra and Luna, all requested `xhigh` | 125.731703197 | Reused manager and worker contexts, actual follow-up briefing, returned work and Sol integration through final output. |

The same-input short packet's team/solo elapsed ratio is 0.4114821112. The context conditions differ as specified in the table; this is one measured completed packet. The source specification SHA-256 is `ddfb068e850078a5edb6397eeed8eec81b8dd3cd4489d70ba2532fd28ad6ebdc`; routine rows `58c3341207b97a47b15e9d3e57edac89f652577f45ba62da60872fe9c85d1740`; faulty module `1439e187cfaa130e9839858ebef585ce3131a94053e18e09520795bd80b394bd`. The two conditions retain original launch identities, artifacts, actual CLI returns and timestamps in the task record. Requested and observed model/effort fields are separate; observed fields, tokens and allowance values were absent from this host's returns.

An earlier source-materialization failure consumed 74.533719014 seconds before the existing state entry could execute; the upstream bytes were restored. Its prepared-code continuation took 23.43408731 seconds and is retained as rehearsal history. The fresh solo condition above starts independently after restoration and reads neither rehearsal nor team outputs.

### Extended real-source development and continuation

The extended task consumes the same immutable 157-file source snapshot, content SHA-256 `c46b7b5ce8054457c423fb5e7115cac149edfda421fb6f67d2fcda3f23bbfacf`, and fixed task SHA-256 `6dee412893843db0214bcd103c4852cf5c29f49048b867f88ab40522b391199b`. It traces CORE, TEAM, registry closure, native templates, the real exporter and its consumers; repairs a real configuration omission; authors source-backed instructions; runs the affected real-registry regressions; then continues from retained deployed output through installed-layout exports.

Both conditions add the same four existing rule dependencies to the existing configuration condition. Both produce source-identical three-child TOMLs and primary template in flat/deployed form, verify source/output identities, keep ordinary bounded snapshots scoped, and preserve completed first exports during installed roundtrip. Existing exporter production code remains sufficient. The adopted release combines that identical registry fix, the solo regression's direct temporary-directory structure, and the team's configuration/source-synthesis text.

| Actual extended condition | Elapsed seconds | Delegations / execution agents | Returned correction requests | Completed evidence |
| --- | ---: | --- | ---: | --- |
| Fresh solo Sol, requested `gpt-6.1-sol`/`xhigh` | 404.985293961 | 0 / 1 | 0 | Three phase-1 focused cases, two continuation cases, four retained configuration exports and all source/output identities. |
| Warm Sol manager with Terra and Luna, all requested `xhigh` | 309.435363058 | 2 / 3 | 0 | Registry/test implementation, mechanical mapping extraction, Sol-authored synthesis, installed continuation and 72 preserved first-export files. |

The extended elapsed ratio is 0.7640656776. The clocks cover each actual completed development and continuation task. The team reconciled one read-version difference: Luna inspected the working registry after Terra applied the fix; the immutable input retains its original `integration.all`-only condition, and the completed working condition has five rules. This reconciliation preserved the fixed specification and used the actual read versions. The short packet likewise uses zero delegations/one execution agent for solo and two delegations/three execution agents for the team, with zero returned correction requests in both completed conditions. The transport-only host primary is outside these execution-agent counts.

These completed development tasks took minutes. The measured clocks and artifacts establish their respective scopes; observed model/effort, token, credit and allowance fields remain null in the source records. No additional benchmark trial or allowance estimate was produced.

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
