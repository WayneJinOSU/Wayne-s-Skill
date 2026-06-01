#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export GIT_CEILING_DIRECTORIES="${GIT_CEILING_DIRECTORIES:-$(dirname "$ROOT_DIR")}"
STATE_DIR="${RESEARCH_QUEUE_STATE_DIR:-$ROOT_DIR/.codex_research}"
LOCK_DIR="$STATE_DIR/research_queue_worker.lock"
LOG_DIR="$STATE_DIR/logs"
RUN_LOG="$LOG_DIR/research_queue_worker.log"
TASKS_DIR="${TASKS_DIR:-$ROOT_DIR/tasks}"
TASKS_PER_PASS="${TASKS_PER_PASS:-1}"

mkdir -p "$STATE_DIR" "$LOG_DIR"

is_alive() {
  local pid="${1:-}"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
  startup_pid="$(cat "$LOCK_DIR/startup_pid" 2>/dev/null || true)"
  if is_alive "$pid"; then
    echo "research queue already running: pid=$pid"
    exit 0
  fi
  if is_alive "$startup_pid"; then
    echo "research queue startup already running: pid=$startup_pid"
    exit 0
  fi

  echo "removing stale research queue lock: $LOCK_DIR" >&2
  rm -rf "$LOCK_DIR"
  mkdir "$LOCK_DIR"
fi

echo "$$" > "$LOCK_DIR/startup_pid"
RESEARCH_QUEUE_IGNORE_STARTUP_PID=1 RESEARCH_QUEUE_SUPPRESS_STALE_LOCK_NOTICE=1 "$ROOT_DIR/scripts/check_research_queue_health.sh" --mark-stale || true

{
  echo "kick_at=$(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "root_dir=$ROOT_DIR"
  echo "tasks_dir=$TASKS_DIR"
  echo "tasks_per_pass=$TASKS_PER_PASS"
} > "$LOCK_DIR/meta"

nohup "$ROOT_DIR/scripts/research_queue_worker_daemon.sh" >> "$RUN_LOG" 2>&1 < /dev/null &

worker_pid="$!"
echo "$worker_pid" > "$LOCK_DIR/pid"
rm -f "$LOCK_DIR/startup_pid"
echo "research queue kicked: pid=$worker_pid"
