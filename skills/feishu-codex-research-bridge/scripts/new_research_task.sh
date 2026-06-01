#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASKS_DIR="${TASKS_DIR:-$ROOT_DIR/tasks}"

skill="auto"
status="queued"
declare -a positional=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      if [[ $# -lt 2 ]]; then
        echo "--skill requires a value" >&2
        exit 1
      fi
      skill="$2"
      shift 2
      ;;
    --paused)
      status="paused"
      shift
      ;;
    -h|--help)
      echo "Usage: scripts/new_research_task.sh [--skill auto|supply-chain-agentic-research|chassis-growth-agentic-research|equity-catalyst-tracker|growth-stock-valuation|industry-chain-agentic-research] [--paused] TASK_NAME [TASK_DESCRIPTION]" >&2
      exit 0
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        positional+=("$1")
        shift
      done
      ;;
    *)
      positional+=("$1")
      shift
      ;;
  esac
done

if [[ "${#positional[@]}" -lt 1 ]]; then
  echo "Usage: scripts/new_research_task.sh [--skill auto|supply-chain-agentic-research|chassis-growth-agentic-research|equity-catalyst-tracker|growth-stock-valuation|industry-chain-agentic-research] [--paused] TASK_NAME [TASK_DESCRIPTION]" >&2
  exit 1
fi

task_name="${positional[0]}"
task_description="${positional[*]:1}"
date_prefix="$(date '+%Y-%m-%d')"

safe_name="$(printf "%s" "$task_name" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[[:space:]]+/_/g; s#[/:]+#_#g; s/[^[:alnum:]_.\-\x80-\xff]+/_/g; s/_+/_/g; s/^_//; s/_$//')"

task_dir="$TASKS_DIR/${date_prefix}_${safe_name}"

if [[ -e "$task_dir" ]]; then
  echo "Task already exists: $task_dir" >&2
  exit 1
fi

mkdir -p "$task_dir/sources"
cp "$TASKS_DIR/_template/brief.md" "$task_dir/brief.md"
printf "%s\n" "$status" > "$task_dir/status"
printf "%s\n" "$skill" > "$task_dir/skill"

tmp_file="$(mktemp)"
awk -v name="$task_name" -v desc="$task_description" -v skill="$skill" '
  /^# 任务名称$/ {
    print "# " name
    next
  }
  /^- 公司\/行业：$/ {
    print "- 公司/行业：" name
    next
  }
  /^- 推荐 skill：/ {
    print "- 推荐 skill：" skill
    next
  }
  /^## 核心问题$/ {
    print
    if (desc != "") {
      print ""
      print desc
      next
    }
  }
  { print }
' "$task_dir/brief.md" > "$tmp_file"
mv "$tmp_file" "$task_dir/brief.md"

cat <<EOF
Created queued research task:
$task_dir

Edit brief:
$task_dir/brief.md

Wake queue:
$ROOT_DIR/scripts/kick_research_queue.sh
EOF
