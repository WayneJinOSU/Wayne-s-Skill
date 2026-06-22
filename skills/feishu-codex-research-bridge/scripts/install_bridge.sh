#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-$PWD}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Target directory not found: $TARGET_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR/scripts" "$TARGET_DIR/tasks/_template" "$TARGET_DIR/.codex_research/logs"

for file in \
  feishu_codex_bridge.mjs \
  new_research_task.sh \
  kick_research_queue.sh \
  research_queue_worker_daemon.sh \
  run_research_queue.sh \
  check_research_queue_health.sh \
  check_skill_drift.sh \
  notify_research_result.sh
do
  cp "$SKILL_DIR/scripts/$file" "$TARGET_DIR/scripts/$file"
done

cp "$SKILL_DIR/assets/tasks/_template/brief.md" "$TARGET_DIR/tasks/_template/brief.md"
cp "$SKILL_DIR/assets/tasks/_template/status" "$TARGET_DIR/tasks/_template/status"

chmod +x \
  "$TARGET_DIR/scripts/new_research_task.sh" \
  "$TARGET_DIR/scripts/kick_research_queue.sh" \
  "$TARGET_DIR/scripts/research_queue_worker_daemon.sh" \
  "$TARGET_DIR/scripts/run_research_queue.sh" \
  "$TARGET_DIR/scripts/check_research_queue_health.sh" \
  "$TARGET_DIR/scripts/check_skill_drift.sh" \
  "$TARGET_DIR/scripts/notify_research_result.sh"

echo "Installed Feishu Codex research bridge into: $TARGET_DIR"
echo "Next: LARK_BRIDGE_CWD=$TARGET_DIR node scripts/feishu_codex_bridge.mjs --dry-run"
