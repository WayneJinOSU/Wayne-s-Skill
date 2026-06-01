# Bridge Installation Reference

## Preconditions

- `lark-cli` is installed and authenticated.
- The Feishu bot has `im.message.receive_v1` events enabled.
- The bot is in the target research group.
- `codex exec` works on the machine.
- The target repo has access to the research skills that queued tasks should call.

Useful checks:

```bash
lark-cli auth status
lark-cli event schema im.message.receive_v1 --json
codex --help
```

## Install Layout

Install these paths into the target repository:

```text
scripts/feishu_codex_bridge.mjs
scripts/new_research_task.sh
scripts/kick_research_queue.sh
scripts/research_queue_worker_daemon.sh
scripts/run_research_queue.sh
scripts/check_research_queue_health.sh
scripts/notify_research_result.sh
tasks/_template/brief.md
tasks/_template/status
```

The bridge creates runtime state under:

```text
.codex_research/feishu_bridge/
.codex_research/logs/
.codex_research/research_queue_worker.lock/
tasks/<date>_<task>/
```

## Run

Start the listener:

```bash
LARK_BRIDGE_CWD=/path/to/repo node scripts/feishu_codex_bridge.mjs
```

Dry-run event consumption without replying or running Codex:

```bash
LARK_BRIDGE_CWD=/path/to/repo node scripts/feishu_codex_bridge.mjs --dry-run
```

Manually wake the queue:

```bash
scripts/kick_research_queue.sh
```

## Feishu Usage

Natural-language task:

```text
/投研 选择合适的skill投研北方华创，启动subagent
```

Explicit task:

```text
/投研 new 北方华创 supply-chain-agentic-research 做正式深度报告，启动subagent
```

Queue inspection:

```text
/投研 list
/投研 status 北方华创
```

## Delivery Semantics

For group-created tasks, the result is sent back to the source group.

For p2p-created tasks, the result is sent to `LARK_RESEARCH_NOTIFY_CHAT_ID`.

On successful completion, `run_research_queue.sh` writes `output_manifest.json` and calls `notify_research_result.sh`. The notifier sends a status message, chooses the final/core report from `research_artifacts/`, converts Markdown to PDF when needed, then sends a Drive PDF link by default.

## Queue Safety

- `kick_research_queue.sh` owns startup locking.
- `research_queue_worker_daemon.sh` loops one task per pass.
- `run_research_queue.sh` executes at most `MAX_TASKS` per pass.
- `check_research_queue_health.sh --mark-stale` is only for confirmed dead workers.
- Keep all entry points behind `kick_research_queue.sh`; this prevents Feishu events and scheduled automation from racing.

## Migration Notes

After copying the scripts into a new repo:

1. Update `LARK_RESEARCH_NOTIFY_CHAT_ID`.
2. Confirm `GIT_CEILING_DIRECTORIES` does not allow Codex to scan a huge parent Git repo.
3. Start the bridge in dry-run mode.
4. Send a test `/投研 ...` message.
5. Confirm the task appears in `tasks/`.
6. Kick the queue and verify `codex exec` starts inside the task directory.
7. Verify a small Markdown report can be converted and posted to Feishu.
