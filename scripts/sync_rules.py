"""Validate compact AI policy pointers and optional reference repositories."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
POINTER = (
    "# econ-project AI rules\n\n"
    "Read and follow `.cursorrules`; it is the single authoritative policy.\n"
    "Do not duplicate or extend its rules in this file.\n"
)
POINTER_PATHS = (
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("CODEX.md"),
    Path(".agents/AGENTS.md"),
    Path(".claude/AGENTS.md"),
    Path(".clinerules"),
    Path(".windsurfrules"),
    Path(".antigravityrules"),
)
OPTIONAL_REFERENCES = (
    Path(".resources/econ-ai/econ-writing-skill"),
    Path(".resources/econ-ai/AI-research-feedback"),
    Path(".resources/econ-ai/awesome-causal-inference"),
    Path(".resources/econ-ai/awesome-econ-ai-stuff"),
    Path(".resources/econ-ai/awesome-ai-for-economists"),
    Path(".resources/research-ai/academic-research-skills"),
    Path(".resources/research-ai/ECC"),
)


def env_flag(*, name: str) -> bool:
    """Return whether an environment variable contains a truthy value."""
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def validate_content(path: Path, expected: str) -> list[str]:
    """Report a missing compact pointer or content drift."""
    if not path.is_file():
        return [f"{path}: compact pointer is missing"]
    if path.read_text(encoding="utf-8") != expected:
        return [f"{path}: content differs from the compact pointer"]
    return []


def validate_optional_content(path: Path, expected: str) -> list[str]:
    """Validate an optional pointer only when it exists."""
    if not path.exists():
        return []
    return validate_content(path, expected)


def validate_reference(path: Path) -> list[str]:
    """Report a missing or incomplete optional reference clone."""
    if not path.is_dir():
        return [f"{path}: required AI reference is missing"]
    if not (path / ".git").exists():
        return [f"{path}: AI reference is not a Git clone"]
    return []


def main() -> int:
    errors: list[str] = []

    if not (PROJECT_ROOT / ".cursorrules").is_file():
        errors.append(
            f"{PROJECT_ROOT / '.cursorrules'}: authoritative policy is missing"
        )

    for relative_path in POINTER_PATHS:
        errors.extend(validate_content(PROJECT_ROOT / relative_path, POINTER))

    if env_flag(name="ECC_REQUIRE_AI_REFERENCES"):
        for relative_path in OPTIONAL_REFERENCES:
            errors.extend(validate_reference(PROJECT_ROOT / relative_path))

    if errors:
        print("AI rule configuration check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AI rule configuration check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
