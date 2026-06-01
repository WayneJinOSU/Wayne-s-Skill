---
name: feishu-codex-research-bridge
description: "Build, migrate, inspect, and operate the local Feishu-to-Codex research bridge: Feishu bot messages create queued research tasks, a serialized worker runs Codex with research skills, final reports are converted to PDF or Drive links, and results are sent back to a Feishu group. Use when the user mentions 飞书/Codex 桥梁, 飞书投研队列, lark-cli event consume, /投研, queue worker, report delivery to Feishu, or migrating this bridge to another repository."
---

# Feishu Codex Research Bridge

Use this skill when the user wants Feishu to be the task intake surface and Codex to be the execution engine for long-running research tasks.

## Core Model

The intended chain is:

```text
Feishu message
-> lark-cli event consume
-> scripts/feishu_codex_bridge.mjs
-> tasks/<task>/brief.md + notify.json
-> scripts/kick_research_queue.sh
-> serialized worker lock
-> scripts/run_research_queue.sh
-> codex exec in the task directory
-> research_artifacts/
-> scripts/notify_research_result.sh
-> Feishu group message / Drive PDF link
```

Keep the bridge narrow:

- Feishu is only the task entrance and result notification surface.
- Codex does natural-language understanding, skill selection, subagent decisions, and report writing.
- The queue is serialized by `research_queue_worker.lock`; do not run long research tasks directly from the event listener.
- Natural-language `/投研 ...` tasks must still be recorded under `tasks/`.
- Final research outputs belong under each task's `research_artifacts/`.

## Bundled Scripts

This skill carries the reusable bridge scripts in `scripts/` and the task template in `assets/tasks/_template/`.

To install or refresh them in a target repository, run:

```bash
bash /path/to/this/skill/scripts/install_bridge.sh /path/to/target/repo
```

If the install script is missing or needs changes, read `references/bridge-installation.md` and then copy the bundled scripts/templates into the target repo with the same paths.

## Operating Commands

From the target repository root:

```bash
node scripts/feishu_codex_bridge.mjs
scripts/kick_research_queue.sh
scripts/check_research_queue_health.sh
scripts/new_research_task.sh "任务名" "任务描述"
```

For background operation, prefer a supervised shell/session and logs under `.codex_research/logs/`.

## Health Checks

When the user asks what is running:

1. Run `scripts/check_research_queue_health.sh`.
2. List task statuses from `tasks/*/status`.
3. Check real processes with `ps` for `feishu_codex_bridge`, `lark-cli event consume`, `research_queue_worker`, `run_research_queue`, and `codex exec`.
4. Inspect the current task's `run.log` and `research_artifacts/`.

Do not mark `running` tasks stale unless the worker and `codex exec` are confirmed dead or the user explicitly asks to clear/retry.

## Important Configuration

Common environment variables:

- `LARK_RESEARCH_TRIGGER`: default `/投研`
- `LARK_RESEARCH_NOTIFY_CHAT_ID`: default group for p2p-created tasks
- `LARK_BRIDGE_CWD`: target repository root
- `LARK_BRIDGE_CONSUME_AS`: usually `bot`
- `LARK_BRIDGE_REPLY_AS`: usually `bot`
- `RESEARCH_TASK_TIMEOUT_SECONDS`: default long task timeout
- `GIT_CEILING_DIRECTORIES`: set to the parent of the target repo to avoid accidental home-level Git discovery

For detailed setup, read `references/bridge-installation.md`.
