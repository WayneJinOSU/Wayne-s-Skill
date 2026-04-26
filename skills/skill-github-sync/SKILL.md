---
name: skill-github-sync
description: Sync local Codex skills from ~/.codex/skills into a GitHub skills repository, update README, commit, and optionally push.
---

# Skill GitHub Sync

## Overview

Use this skill when the user wants to maintain local Codex skills in a GitHub repository. It syncs selected active skills from `~/.codex/skills` into a repo `skills/` directory, updates the repo index, checks for obvious secret patterns, commits the changes, and can push over the repo's configured remote.

## Default Repo

For Wayne's setup, use this repository unless the user gives another path:

```text
/Users/a/Documents/Codex/2026-04-24/skill-skill-1-4-8-17/Wayne-s-Skill-ssh
```

The remote should use SSH:

```text
git@github.com:WayneJinOSU/Wayne-s-Skill.git
```

## Workflow

1. Confirm the repo exists and is clean enough to work with.
2. Run `scripts/sync_skills.py` from this skill.
3. Review the changed files and secret-scan warnings.
4. Commit with a clear message.
5. Push only when the user asked for GitHub upload or when the request clearly implies it.

## Commands

Sync all active local skills, commit, and push:

```bash
python3 ~/.codex/skills/skill-github-sync/scripts/sync_skills.py \
  --repo /Users/a/Documents/Codex/2026-04-24/skill-skill-1-4-8-17/Wayne-s-Skill-ssh \
  --commit \
  --push
```

Sync only one skill:

```bash
python3 ~/.codex/skills/skill-github-sync/scripts/sync_skills.py \
  --repo /Users/a/Documents/Codex/2026-04-24/skill-skill-1-4-8-17/Wayne-s-Skill-ssh \
  --skill local-bank-research \
  --commit \
  --push
```

Preview without writing:

```bash
python3 ~/.codex/skills/skill-github-sync/scripts/sync_skills.py \
  --repo /Users/a/Documents/Codex/2026-04-24/skill-skill-1-4-8-17/Wayne-s-Skill-ssh \
  --dry-run
```

## Exclusions

By default, do not sync:

- `.system`
- `codex-primary-runtime`
- directories ending in `.bak` or containing `.bak-`
- hidden directories

## Notes

- The script intentionally does not delete repo skills that no longer exist locally unless `--prune` is passed.
- If the secret scan reports a real credential, stop and ask the user before committing.
- If Git push fails due to SSH auth, ask the user to run `ssh-add ~/.ssh/id_rsa`.
