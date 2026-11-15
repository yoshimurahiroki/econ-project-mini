# Research workflow

Follow [AGENTS.md](../AGENTS.md) for the current research workflow and proportional verification.

## Installed agent skill packs

The workspace includes three additional skill packs under `.github/agent-plugins/`.
Use their local source instead of downloading or reconstructing them:

- pstack: `.github/agent-plugins/pstack/skills/poteto-mode/SKILL.md`
- Matt Pocock skills: `.github/agent-plugins/mattpocock-skills/skills/`
- ponytail: `.github/agent-plugins/ponytail/skills/ponytail/SKILL.md`

For rigorous software-engineering work, use pstack's `poteto-mode` as the workflow
entry point. Use Matt Pocock skills when the request matches one of its named
engineering or productivity skills. Apply ponytail's always-on rules when the
request calls for its review, audit, or minimal-implementation discipline.
Keep the economics workflow in `AGENTS.md` authoritative for research tasks.

The same local skill directories are exposed to Claude Code through
`.claude/skills/` and to Codex through `.agents/skills/`.
