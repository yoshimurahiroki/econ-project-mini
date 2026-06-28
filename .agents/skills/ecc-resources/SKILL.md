---
name: ecc-resources
description: Use to inspect local affaan-m/ECC skills, rules, hooks, and examples as a reference library without installing or preloading ECC into the active agent surface.
origin: econ-project
---

# ECC Resources

Lightweight index for the local `affaan-m/ECC` reference clone.

## Use For

- Inspecting ECC skill, rule, hook, plugin, or agent-surface examples.
- Comparing Codex, Claude, Cursor, Gemini, or Antigravity configuration shapes.
- Designing local lightweight indexes while keeping this project cloud-only.

## Reference loading

Do not read the whole repository. Open exactly one starting path:

- Repository overview:
  `.resources/research-ai/ECC/README.md`
- Codex plugin reference:
  `.resources/research-ai/ECC/.codex-plugin/README.md`
- Claude plugin reference:
  `.resources/research-ai/ECC/.claude-plugin/README.md`
- Rules examples:
  `.resources/research-ai/ECC/.cursor/rules/`
- Skill examples:
  `.resources/research-ai/ECC/.agents/skills/`

Use `rg` to find a specific skill, rule, or hook before opening files.

## Boundaries

- Treat ECC as reference material, not an installer.
- Do not copy upstream MCP, hook, Git, worktree, or multi-agent automation into
  this project unless the user explicitly asks for that specific workflow.
- Keep active project rules compact and authoritative in `.cursorrules`.
- Prefer project-native economics skills over broad ECC skills for research
  writing, causal inference, and paper review tasks.
