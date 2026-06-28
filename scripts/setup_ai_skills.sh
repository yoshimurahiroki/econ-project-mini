#!/bin/bash
# Ensure economics AI references are available without preloading them.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ECON_RESOURCE_ROOT="$PROJECT_ROOT/.resources/econ-ai"
RESEARCH_RESOURCE_ROOT="$PROJECT_ROOT/.resources/research-ai"

if [ "${ECC_FETCH_AI_REFERENCES:-0}" != "1" ]; then
    echo "Skipping optional AI reference clones. Set ECC_FETCH_AI_REFERENCES=1 to fetch them."
    bash "$SCRIPT_DIR/setup_ide_mcp.sh" --check
    echo "AI skill configuration check passed."
    exit 0
fi

mkdir -p "$ECON_RESOURCE_ROOT" "$RESEARCH_RESOURCE_ROOT"

clone_or_update() {
    local repo="$1"
    local name="$2"
    local root="$3"
    local target="$root/$name"

    if [ -d "$target/.git" ]; then
        if [ "${ECC_UPDATE_SKILLS:-0}" = "1" ]; then
            echo "Updating $name..."
            env GIT_TERMINAL_PROMPT=0 git -C "$target" fetch --depth 1 origin --quiet || true
            default_branch="$(git -C "$target" remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')"
            if [ -n "$default_branch" ]; then
                git -C "$target" reset --hard "origin/$default_branch" --quiet || true
            fi
        else
            echo "Found $name."
        fi
        return
    fi

    echo "Cloning $name..."
    env GIT_TERMINAL_PROMPT=0 git clone --depth 1 "https://github.com/$repo.git" "$target" --quiet
}

clone_or_update "hanlulong/econ-writing-skill" "econ-writing-skill" "$ECON_RESOURCE_ROOT"
clone_or_update "claesbackman/AI-research-feedback" "AI-research-feedback" "$ECON_RESOURCE_ROOT"
clone_or_update "matteocourthoud/awesome-causal-inference" "awesome-causal-inference" "$ECON_RESOURCE_ROOT"
clone_or_update "meleantonio/awesome-econ-ai-stuff" "awesome-econ-ai-stuff" "$ECON_RESOURCE_ROOT"
clone_or_update "hanlulong/awesome-ai-for-economists" "awesome-ai-for-economists" "$ECON_RESOURCE_ROOT"
clone_or_update "Imbad0202/academic-research-skills" "academic-research-skills" "$RESEARCH_RESOURCE_ROOT"
clone_or_update "affaan-m/ECC" "ECC" "$RESEARCH_RESOURCE_ROOT"

echo "Economics AI references are available under $ECON_RESOURCE_ROOT."
echo "Research AI references are available under $RESEARCH_RESOURCE_ROOT."
bash "$SCRIPT_DIR/setup_ide_mcp.sh" --check
echo "AI skill configuration check passed."
