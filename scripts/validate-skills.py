#!/usr/bin/env python3
"""
Validate every skill in skills/* — checks:

1. Every skill directory contains a SKILL.md.
2. SKILL.md starts with a YAML frontmatter block (--- ... ---).
3. Frontmatter has at minimum `name:` and `description:` keys.
4. `name:` matches the directory name (so the agent's host doesn't
   load a skill under a name that contradicts the directory).
5. `description:` is non-empty and >= 30 chars (description is what the
   agent matches against user intent — terse one-liners get missed).

Run from repo root: `python3 scripts/validate-skills.py`.

Exit code 0 = all good, 1 = at least one skill failed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def parse_frontmatter(path: Path) -> Optional[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    block = text[4:end]
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        print(f"error: {skills_dir} does not exist", file=sys.stderr)
        return 1

    failed: list[str] = []
    skill_dirs = sorted([d for d in skills_dir.iterdir() if d.is_dir()])
    if not skill_dirs:
        print(f"error: no skills found under {skills_dir}", file=sys.stderr)
        return 1

    for d in skill_dirs:
        skill_md = d / "SKILL.md"
        if not skill_md.is_file():
            failed.append(f"{d.name}: missing SKILL.md")
            continue
        fm = parse_frontmatter(skill_md)
        if fm is None:
            failed.append(f"{d.name}: SKILL.md has no YAML frontmatter")
            continue
        name = fm.get("name", "")
        desc = fm.get("description", "")
        if not name:
            failed.append(f"{d.name}: frontmatter missing `name:`")
        elif name != d.name:
            failed.append(
                f"{d.name}: frontmatter name `{name}` != directory `{d.name}`"
            )
        if not desc:
            failed.append(f"{d.name}: frontmatter missing `description:`")
        elif len(desc) < 30:
            failed.append(
                f"{d.name}: description too terse "
                f"({len(desc)} chars; agents match on it — make it specific)"
            )
        if name and desc and name == d.name and len(desc) >= 30:
            print(f"  ok  {d.name}")

    if failed:
        print("", file=sys.stderr)
        print("Validation failed:", file=sys.stderr)
        for f in failed:
            print(f"  ✗ {f}", file=sys.stderr)
        return 1

    print()
    print(f"All {len(skill_dirs)} skill(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
