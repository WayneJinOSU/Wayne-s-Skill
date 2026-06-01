#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${RESEARCH_QUEUE_STATE_DIR:-$ROOT_DIR/.codex_research}"
LOCK_DIR="$STATE_DIR/research_queue_worker.lock"
TASKS_DIR="${TASKS_DIR:-$ROOT_DIR/tasks}"
MARK_STALE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mark-stale)
      MARK_STALE=true
      shift
      ;;
    -h|--help)
      echo "Usage: scripts/check_research_queue_health.sh [--mark-stale]" >&2
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

is_alive() {
  local pid="${1:-}"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

worker_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
startup_pid="$(cat "$LOCK_DIR/startup_pid" 2>/dev/null || true)"
worker_alive=false
startup_alive=false
if is_alive "$worker_pid"; then
  worker_alive=true
fi
if [[ "${RESEARCH_QUEUE_IGNORE_STARTUP_PID:-0}" != "1" ]] && is_alive "$startup_pid"; then
  startup_alive=true
fi

status_count() {
  local wanted="$1"
  local count
  count="$(find "$TASKS_DIR" -mindepth 2 -maxdepth 2 -name status -type f -exec sh -c '
    wanted="$1"
    shift
    count=0
    for f do
      status="$(tr -d "[:space:]" < "$f")"
      [ "$status" = "$wanted" ] && count=$((count + 1))
    done
    printf "%s\n" "$count"
  ' sh "$wanted" {} + 2>/dev/null || true)"
  printf "%s\n" "${count:-0}"
}

running_files="$(
  find "$TASKS_DIR" -mindepth 2 -maxdepth 2 -name status -type f -exec sh -c '
    for f do
      [ "$(tr -d "[:space:]" < "$f")" = running ] && printf "%s\n" "$f"
    done
  ' sh {} + 2>/dev/null || true
)"

echo "worker_alive=$worker_alive${worker_pid:+ pid=$worker_pid}"
echo "queued=$(status_count queued)"
echo "running=$(status_count running)"
echo "failed=$(status_count failed)"
echo "stale=$(status_count stale)"
echo "timeout=$(status_count timeout)"

if [[ "$worker_alive" == true ]]; then
  exit 0
fi

if [[ "$startup_alive" == true ]]; then
  echo "startup_alive=true pid=$startup_pid"
  exit 0
fi

if [[ -d "$LOCK_DIR" && "${RESEARCH_QUEUE_SUPPRESS_STALE_LOCK_NOTICE:-0}" != "1" ]]; then
  echo "stale_lock=$LOCK_DIR"
fi

if [[ -z "$running_files" ]]; then
  exit 0
fi

if [[ "$MARK_STALE" != true ]]; then
  echo "running tasks exist but worker is not alive; pass --mark-stale to mark them stale"
  printf "%s\n" "$running_files"
  exit 1
fi

while IFS= read -r status_file; do
  [[ -z "$status_file" ]] && continue
  task_dir="$(dirname "$status_file")"
  task_name="$(basename "$task_dir")"
  stale_at="$(date '+%Y-%m-%d %H:%M:%S %z')"

  printf "stale\n" > "$status_file"
  printf "%s\n" "$stale_at" > "$task_dir/finished_at"
  printf "stale\n" > "$task_dir/exit_code"
  {
    echo ""
    echo "[$stale_at] marked stale: status was running but research queue worker is not alive."
  } >> "$task_dir/run.log"

  echo "marked stale: $task_name"

  if [[ -f "$task_dir/notify.json" && -x "$ROOT_DIR/scripts/notify_research_result.sh" ]]; then
    "$ROOT_DIR/scripts/notify_research_result.sh" "$task_dir" >> "$task_dir/notify.log" 2>&1 || {
      echo "[$task_name] stale notification failed; see $task_dir/notify.log" >&2
    }
  fi
done <<< "$running_files"
