#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export GIT_CEILING_DIRECTORIES="${GIT_CEILING_DIRECTORIES:-$(dirname "$ROOT_DIR")}"
STATE_DIR="${RESEARCH_QUEUE_STATE_DIR:-$ROOT_DIR/.codex_research}"
LOCK_DIR="$STATE_DIR/research_queue_worker.lock"
TASKS_DIR="${TASKS_DIR:-$ROOT_DIR/tasks}"
TASKS_PER_PASS="${TASKS_PER_PASS:-1}"

trap 'rm -rf "$LOCK_DIR"' EXIT

echo "[$(date '+%Y-%m-%d %H:%M:%S %z')] worker started"
exit_code=0

while true; do
  set +e
  pass_output="$(TASKS_DIR="$TASKS_DIR" MAX_TASKS="$TASKS_PER_PASS" "$ROOT_DIR/scripts/run_research_queue.sh" 2>&1)"
  pass_code=$?
  set -e

  printf "%s\n" "$pass_output"

  if [[ "$pass_code" -ne 0 ]]; then
    exit_code="$pass_code"
    break
  fi

  if grep -q "No queued tasks found." <<< "$pass_output"; then
    break
  fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S %z')] worker finished exit_code=$exit_code"
exit "$exit_code"
