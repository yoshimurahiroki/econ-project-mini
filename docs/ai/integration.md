# Project integration

Repository skills run in the coding environment. Project attachments are snapshots identified in SOURCE.md. A repository task uses the current policy and the files relevant to the request.

## Common core

[econ-project-mini](https://github.com/yoshimurahiroki/econ-project-mini) is the editing source for the common policy, skills, references, host pointers, indexes, Project templates and exporter. The explicit `COMMON_PATHS` allowlist in [sync_common_core.py](../../scripts/sync_common_core.py) defines the same relative paths copied to econ-project and Ruan. Project context, integration prose, source history, study records, environments and execution recipes remain project-owned.

Compare and apply when preparing publication of a common-core change. Use the actual destination HEADs for `--expect-head`; this example uses the refactor's recorded baselines.

```sh
cd /tmp/econ-project-mini-instructions-20261008
python scripts/sync_common_core.py --source . \
  --target /tmp/econ-project-instructions-20261008 \
  --target /tmp/ruan-literature-20261005

python scripts/sync_common_core.py --source . \
  --target /tmp/econ-project-instructions-20261008 \
  --target /tmp/ruan-literature-20261005 --apply \
  --expect-head econ-project=91aad0bb9c15583d8ca2efce9303642043cfc7a5 \
  --expect-head Ruan=af5a07cfcc0ac00a9a0e556520623fc2673f97bf
```

Comparison is read-only. The script records copied source bytes in the destinations' managed common-core receipt; the receipt is the only synchronized part of this document. Exit codes are 0 for equality or successful application, 1 for comparison differences and 2 for a refused or invalid operation. Ordinary task startup and environment setup run neither synchronization nor export.

## Existing R00-R08 Project

```sh
python scripts/export_project.py --profile bridge --output /tmp/econ-bridge-new
```

Keep the unchanged existing R00-R08 method attachments. For a complete instruction-field replacement, paste PROJECT_INSTRUCTIONS.txt. To update a separately maintained field, replace its bridge block with BRIDGE_INSTRUCTIONS.txt and remove conflicting inherited common-policy, profile and final-dispatch text. Attach the exported files. ECON_INDEX.md records their roles; supplied R00_ROUTER.md resolves the existing research method for the requested deliverable. An explicit native-provider request uses the exported native fallback for that deliverable.

## Standalone Project

```sh
python scripts/export_project.py --profile standalone --output /tmp/econ-all-new
python scripts/export_project.py --profile standalone --skills econ-paper econ-design \
  --output /tmp/econ-subset-new
```

Paste PROJECT_INSTRUCTIONS.txt into the field and attach the other exported files. Standalone without `--task` or `--skills` retains all 11 skill bodies and their references. `--skills` selects an available subset. A study entry point is included when declared by the project block.

## Task snapshots

```sh
python scripts/export_project.py --profile standalone --task econ-paper \
  --references .agents/skills/econ-workflow/references/descriptive-model.md \
  --output /tmp/econ-paper-new
python scripts/export_project.py --profile standalone --task econ-edit \
  --style-profile default-micro --output /tmp/econ-edit-new
```

`--task` selects the deliverable's method role; `--support` names a dependency method and `--references` names an exact repository-relative reference file. Both options are repeatable and require `--task`. `--task` and `--skills` are exclusive. Bridge task snapshots keep the supplied R00-R08 provider and include the selected native body as its available fallback. A requested profile operation selects econ-style.

Task snapshots include the selected bodies, explicit references and applicable writing-profile resources. Inclusion makes a resource available; the current task determines whether it is read. ECON_INDEX.md lists the selected roles and files. Project additions come from the `export-project:v1` block in [repo_context.md](repo_context.md).

Use a fresh output directory outside the repository. The exporter enforces the 8,000-character instruction-field limit. Included links use exported filenames; omitted repository files use their recorded immutable revision. SOURCE.md records source versions, original and generated hashes and snapshot identity, including working-file content. Regenerate the selected snapshot when its source instructions change.

## Custom exemplars

[econ-assertive](../../.agents/skills/econ-assertive/SKILL.md) owns writing-profile selection. The `writing_profile` value in [project context](repo_context.md) records the persistent choice. `--style-profile` selects a snapshot's task profile without changing that value. Writing or wording tasks include the selected profile and default-micro for a needed function absent from it.

To create or revise a profile, request econ-style with the source papers, language and target section. Name a destination to save it; a repository-save request without a path uses docs/ai/custom-style.md. Creation and saving preserve the persistent choice. Change the project-context value only for an explicit request to adopt or switch the profile.

## Handoff

A requested handoff uses the existing task record for the revision, evidence, authorized work, results and next action relevant to the transfer. Keep private data and credentials in their existing storage.
