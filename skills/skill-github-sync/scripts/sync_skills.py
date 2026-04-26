#!/usr/bin/env python3
"""Sync local Codex skills into a GitHub skills repository."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_REPO = Path(
    "/Users/a/Documents/Codex/2026-04-24/skill-skill-1-4-8-17/Wayne-s-Skill-ssh"
)
DEFAULT_SOURCE = Path.home() / ".codex" / "skills"
SKIP_NAMES = {".system", "codex-primary-runtime"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"ghp_[A-Za-z0-9_]+"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def is_active_skill(path: Path) -> bool:
    if not path.is_dir():
        return False
    if path.name in SKIP_NAMES or path.name.startswith("."):
        return False
    if path.name.endswith(".bak") or ".bak-" in path.name:
        return False
    return (path / "SKILL.md").is_file()


def parse_description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    if not match:
        return "Codex skill."
    return match.group(1).strip().strip('"').strip("'")


def list_skills(source: Path, requested: list[str] | None) -> list[Path]:
    if requested:
        skills = [source / name for name in requested]
        missing = [path.name for path in skills if not is_active_skill(path)]
        if missing:
            raise SystemExit(f"Missing or inactive skill(s): {', '.join(missing)}")
        return skills
    return sorted(path for path in source.iterdir() if is_active_skill(path))


def sync_skill(src: Path, dest_root: Path, dry_run: bool) -> None:
    dest = dest_root / src.name
    if dry_run:
        print(f"Would sync {src} -> {dest}")
        return
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"),
    )


def update_readme(repo: Path, skills: list[Path], dry_run: bool) -> None:
    readme = repo / "README.md"
    entries = []
    for skill in sorted(skills, key=lambda item: item.name):
        desc = parse_description(skill / "SKILL.md")
        entries.append(f"- `{skill.name}`: {desc}")

    content = "\n".join(
        [
            "# Wayne's Skill",
            "",
            "Personal Codex skills maintained as versioned assets.",
            "",
            "## Skills",
            "",
            *entries,
            "",
            "## Local install",
            "",
            "Install or update all skills from this repo into Codex:",
            "",
            "```bash",
            "mkdir -p ~/.codex/skills",
            "cp -R skills/* ~/.codex/skills/",
            "```",
            "",
            "Restart Codex after installing or updating skills.",
            "",
        ]
    )
    if dry_run:
        print(f"Would update {readme}")
        return
    readme.write_text(content, encoding="utf-8")


def scan_for_secrets(repo: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted((repo / "skills").rglob("*")):
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line_no = text[: match.start()].count("\n") + 1
                findings.append(f"{path.relative_to(repo)}:{line_no}: {match.group(0)[:80]}")
    return findings


def ensure_repo(repo: Path) -> None:
    if not (repo / ".git").is_dir():
        raise SystemExit(f"Not a git repository: {repo}")
    if not (repo / "skills").exists():
        (repo / "skills").mkdir(parents=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(os.environ.get("WAYNE_SKILL_REPO", DEFAULT_REPO)))
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--skill", action="append", help="Skill name to sync. Repeat to sync multiple.")
    parser.add_argument("--commit", action="store_true", help="Create a git commit after syncing.")
    parser.add_argument("--push", action="store_true", help="Push to the configured git remote after commit.")
    parser.add_argument("--prune", action="store_true", help="Delete repo skills not present in the selected local set.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing files.")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    source = args.source.expanduser().resolve()
    ensure_repo(repo)
    selected = list_skills(source, args.skill)
    dest_root = repo / "skills"

    selected_names = {path.name for path in selected}
    if args.prune and not args.dry_run:
        for existing in dest_root.iterdir():
            if existing.is_dir() and existing.name not in selected_names:
                shutil.rmtree(existing)

    for skill in selected:
        sync_skill(skill, dest_root, args.dry_run)
    repo_skills = sorted(path for path in dest_root.iterdir() if is_active_skill(path))
    update_readme(repo, repo_skills if not args.dry_run else selected, args.dry_run)

    if args.dry_run:
        return 0

    findings = scan_for_secrets(repo)
    if findings:
        print("Potential secret patterns found. Review before committing:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 2

    status = run(["git", "status", "--short"], cwd=repo).stdout.strip()
    if not status:
        print("No changes to commit.")
        return 0

    print(status)
    if args.commit:
        names = ", ".join(sorted(selected_names))
        run(["git", "add", "README.md", "skills"], cwd=repo)
        run(["git", "commit", "-m", f"Sync Codex skills: {names}"], cwd=repo)
        if args.push:
            run(["git", "push", "origin", "main"], cwd=repo)
    elif args.push:
        raise SystemExit("--push requires --commit")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
