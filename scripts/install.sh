#!/usr/bin/env bash
#
# Install FloopFloop agent skills into a Claude skills directory.
#
# Defaults to ~/.claude/skills (user-wide). Pass a path to install
# project-locally:
#
#   ./install.sh                       # ~/.claude/skills
#   ./install.sh ./.claude/skills      # this project's skills
#
set -euo pipefail

DEST="${1:-$HOME/.claude/skills}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -d "$HERE/skills" ]]; then
  echo "error: skills/ directory not found at $HERE — run this from a clone of floop-skills" >&2
  exit 1
fi

mkdir -p "$DEST"

count=0
for skill_dir in "$HERE/skills"/*/; do
  skill_name="$(basename "$skill_dir")"
  if [[ -d "$DEST/$skill_name" ]]; then
    echo "  ↻  $skill_name (overwriting existing)"
    rm -rf "$DEST/$skill_name"
  else
    echo "  +  $skill_name"
  fi
  cp -r "$skill_dir" "$DEST/$skill_name"
  count=$((count + 1))
done

echo ""
echo "Installed $count FloopFloop skill(s) to $DEST"
echo "Restart your agent host (Claude Code / Desktop / Cursor / etc.) to pick them up."
