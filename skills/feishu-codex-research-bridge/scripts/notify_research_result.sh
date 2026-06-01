#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_DIR="${1:-}"

export LANG="${LARK_BRIDGE_LOCALE:-zh_CN.UTF-8}"
export LC_ALL="${LARK_BRIDGE_LOCALE:-zh_CN.UTF-8}"
export LC_CTYPE="${LARK_BRIDGE_LOCALE:-zh_CN.UTF-8}"

if [[ -z "$TASK_DIR" ]]; then
  echo "Usage: scripts/notify_research_result.sh TASK_DIR" >&2
  exit 1
fi

if [[ ! -d "$TASK_DIR" ]]; then
  echo "Task directory not found: $TASK_DIR" >&2
  exit 1
fi

NOTIFY_JSON="$TASK_DIR/notify.json"
MANIFEST_JSON="$TASK_DIR/output_manifest.json"

if [[ ! -f "$NOTIFY_JSON" ]]; then
  echo "notify.json not found: $NOTIFY_JSON" >&2
  exit 1
fi

json_value() {
  local file="$1"
  local expr="$2"
  node - "$file" "$expr" <<'NODE'
const fs = require("node:fs");
const file = process.argv[2];
const expr = process.argv[3];
const data = JSON.parse(fs.readFileSync(file, "utf8"));
let value = data;
for (const key of expr.split(".")) {
  value = value?.[key];
}
if (Array.isArray(value)) {
  console.log(value.join("\n"));
} else if (value !== undefined && value !== null) {
  console.log(String(value));
}
NODE
}

task_name="$(basename "$TASK_DIR")"
status="$(tr -d '[:space:]' < "$TASK_DIR/status" 2>/dev/null || printf unknown)"
selected_skill="$(cat "$TASK_DIR/selected_skill" 2>/dev/null || cat "$TASK_DIR/skill" 2>/dev/null || printf unknown)"
exit_code="$(cat "$TASK_DIR/exit_code" 2>/dev/null || printf unknown)"
finished_at="$(cat "$TASK_DIR/finished_at" 2>/dev/null || printf unknown)"
notify_chat_id="$(json_value "$NOTIFY_JSON" "notify_chat_id")"
notify_as="$(json_value "$NOTIFY_JSON" "notify_as")"
notify_as="${notify_as:-bot}"

if [[ -z "$notify_chat_id" ]]; then
  echo "notify_chat_id is empty in $NOTIFY_JSON" >&2
  exit 1
fi

core_outputs=""
pdf_outputs=""
if [[ -f "$MANIFEST_JSON" ]]; then
  core_outputs="$(json_value "$MANIFEST_JSON" "core_outputs" || true)"
  pdf_outputs="$(json_value "$MANIFEST_JSON" "pdf_outputs" | grep -Ev '/sources?/|/source_(pdfs?|texts?)/' || true)"
fi

notification_files=""
if [[ "$status" == "done" && -f "$MANIFEST_JSON" && "${LARK_RESEARCH_SEND_FILES:-1}" != "0" ]]; then
  notification_files="$(
    node - "$TASK_DIR" "$MANIFEST_JSON" "${LARK_RESEARCH_MAX_FILE_SENDS:-1}" <<'NODE'
const fs = require("node:fs");
const path = require("node:path");

const [taskDir, manifestFile, maxRaw] = process.argv.slice(2);
const maxFiles = Math.max(1, Number(maxRaw || 1));
const manifest = JSON.parse(fs.readFileSync(manifestFile, "utf8"));

function safeRel(file) {
  if (!file || path.isAbsolute(file)) return false;
  const parts = file.split(/[\\/]+/);
  return parts[0] === "research_artifacts" && !parts.includes("..");
}

function existsRel(file) {
  return safeRel(file) && fs.existsSync(path.join(taskDir, file));
}

function uniq(files) {
  return [...new Set(files.filter(existsRel))];
}

function isSourceArtifact(file) {
  return /(?:^|\/)(sources?|source_pdfs?|source_texts?)(?:\/|$)/i.test(file);
}

const coreOutputs = uniq(manifest.core_outputs || []);
const pdfOutputs = uniq(manifest.pdf_outputs || []).filter((file) => !isSourceArtifact(file));
const selectedSkill = String(manifest.selected_skill || "");
const primaryPatterns = {
  "growth-stock-valuation": [/(?:^|\/)[^/]+_valuation_deepdive\.md$/i],
  "supply-chain-agentic-research": [/(?:^|\/)[^/]+_final_report\.md$/i],
  "chassis-growth-agentic-research": [/(?:^|\/)[^/]+_final_report\.md$/i],
  "equity-catalyst-tracker": [/(?:^|\/)[^/]+_integrated_update\.md$/i],
  "industry-chain-agentic-research": [/(?:^|\/)[^/]+_final_report_full\.md$/i],
};
const patterns = primaryPatterns[selectedSkill] || [
  /(?:^|\/)[^/]+_(final_report|final_report_full|integrated_update|valuation_deepdive)\.md$/i,
];
const finalReports = coreOutputs.filter((file) => patterns.some((pattern) => pattern.test(file)));
const fallbackReports = coreOutputs.filter((file) => (
  /(?:^|\/)[^/]+_(executive_summary|plain_investor_guide|valuation_scorecard)\.md$/i.test(file)
));
const reportPdfOutputs = pdfOutputs.filter((file) => (
  /(?:^|\/)[^/]+_(final_report|final_report_full|integrated_update|valuation_deepdive|executive_summary|plain_investor_guide|valuation_scorecard)(?:_feishu)?\.pdf$/i.test(file)
));

const selected = finalReports.length
  ? finalReports
  : (reportPdfOutputs.length ? reportPdfOutputs : (fallbackReports.length ? fallbackReports : coreOutputs));

for (const file of selected.slice(0, maxFiles)) {
  console.log(file);
}
NODE
  )"
fi

final_excerpt=""
if [[ "$status" != "done" && -f "$TASK_DIR/final_message.txt" ]]; then
  final_excerpt="$(head -c "${LARK_RESEARCH_FINAL_EXCERPT_CHARS:-500}" "$TASK_DIR/final_message.txt")"
fi

message="$(
  cat <<EOF
投研任务：$task_name
状态：$status
Skill：$selected_skill
退出码：$exit_code
完成时间：$finished_at
EOF
)"

if [[ -n "$notification_files" ]]; then
  message="$message

将发送：
$notification_files"
  if grep -q '\.md$' <<< "$notification_files"; then
    message="$message
说明：终稿 Markdown 会自动转成 PDF 后发送。"
  fi
fi

if [[ -n "$core_outputs" && "${LARK_RESEARCH_VERBOSE_NOTIFY:-0}" == "1" ]]; then
  message="$message

核心文件：
$core_outputs"
fi

if [[ -n "$pdf_outputs" && "${LARK_RESEARCH_VERBOSE_NOTIFY:-0}" == "1" ]]; then
  message="$message

PDF 文件：
$pdf_outputs"
fi

if [[ -n "$final_excerpt" ]]; then
  message="$message

Codex 最终回复：
$final_excerpt"
fi

cd "$ROOT_DIR"
idempotency_key="research-$(printf "%s" "$TASK_DIR-$status-$exit_code-$finished_at" | shasum | awk '{print $1}')"
dry_run_args=()
if [[ "${LARK_RESEARCH_DRY_RUN:-0}" == "1" ]]; then
  dry_run_args=(--dry-run)
fi
lark-cli im +messages-send \
  --chat-id "$notify_chat_id" \
  --text "$message" \
  --as "$notify_as" \
  ${dry_run_args[@]+"${dry_run_args[@]}"} \
  --idempotency-key "$idempotency_key"

if [[ -n "$notification_files" ]]; then
  file_send_failed=0
  while IFS= read -r rel_file; do
    [[ -n "$rel_file" ]] || continue
    send_rel_file="$rel_file"
    if [[ "$rel_file" == *.md ]]; then
      mkdir -p "$TASK_DIR/.codex_notify_files"
      base_name="$(basename "$rel_file" .md)"
      pdf_base="${base_name}_feishu"
      pdf_abs="$TASK_DIR/.codex_notify_files/${pdf_base}.pdf"
      if [[ ! -f "$pdf_abs" || "$TASK_DIR/$rel_file" -nt "$pdf_abs" ]]; then
        if ! node "$HOME/.codex/skills/markdown-report-pdf/scripts/render_markdown_report_pdf.mjs" \
          --title "$base_name" \
          --subtitle "$task_name" \
          --date "${finished_at:0:10}" \
          --out-dir "$TASK_DIR/.codex_notify_files" \
          --basename "$pdf_base" \
          "$TASK_DIR/$rel_file"; then
          echo "failed to render pdf for: $rel_file" >&2
          file_send_failed=1
          continue
        fi
      fi
      send_rel_file=".codex_notify_files/${pdf_base}.pdf"
    fi
    if [[ "$send_rel_file" == *.pdf && "${LARK_RESEARCH_PDF_DELIVERY:-drive}" == "drive" && "${LARK_RESEARCH_DRY_RUN:-0}" != "1" ]]; then
      echo "uploading PDF to Drive: $send_rel_file" >&2
      upload_output=""
      if upload_output="$(
        cd "$TASK_DIR"
        lark-cli drive +upload \
          --as "${LARK_RESEARCH_DRIVE_UPLOAD_AS:-user}" \
          --file "$send_rel_file" \
          --name "$(basename "$send_rel_file")"
      )"; then
        printf "%s\n" "$upload_output"
        drive_url="$(
          node -e '
const text = process.argv[1] || "";
const positions = [];
for (let i = 0; i < text.length; i += 1) {
  if (text[i] === "{") positions.push(i);
}
for (const pos of positions.reverse()) {
  try {
    const data = JSON.parse(text.slice(pos));
    const url = data?.data?.url;
    if (url) {
      console.log(url);
      process.exit(0);
    }
  } catch {}
}
process.exit(1);
' "$upload_output"
        )" || drive_url=""
        if [[ -n "$drive_url" ]]; then
          lark-cli im +messages-send \
            --chat-id "$notify_chat_id" \
            --text "投研报告 PDF 已上传：$drive_url" \
            --as "$notify_as"
          echo "sent Drive PDF link for: $rel_file"
        else
          echo "Drive upload succeeded but URL was not found for: $rel_file" >&2
          file_send_failed=1
        fi
      else
        printf "%s\n" "$upload_output" >&2
        echo "Drive upload failed: $rel_file" >&2
        file_send_failed=1
      fi
      continue
    fi
    file_key="research-file-$(printf "%s" "$TASK_DIR-$status-$exit_code-$finished_at-$rel_file" | shasum | awk '{print $1}')"
    if (
      cd "$TASK_DIR"
      lark-cli im +messages-send \
        --chat-id "$notify_chat_id" \
        --file "$send_rel_file" \
        --as "$notify_as" \
        ${dry_run_args[@]+"${dry_run_args[@]}"} \
        --idempotency-key "$file_key"
    ); then
      if [[ "${LARK_RESEARCH_DRY_RUN:-0}" == "1" ]]; then
        echo "dry-run file request ok: $rel_file"
      else
        echo "sent file: $rel_file"
      fi
    else
      echo "failed to send file directly: $rel_file" >&2
      if [[ "${LARK_RESEARCH_DRIVE_FALLBACK:-1}" != "0" && "$send_rel_file" == *.pdf && "${LARK_RESEARCH_DRY_RUN:-0}" != "1" ]]; then
        echo "trying Drive upload fallback: $send_rel_file" >&2
        upload_output=""
        if upload_output="$(
          cd "$TASK_DIR"
          lark-cli drive +upload \
            --as "${LARK_RESEARCH_DRIVE_UPLOAD_AS:-user}" \
            --file "$send_rel_file" \
            --name "$(basename "$send_rel_file")"
        )"; then
          printf "%s\n" "$upload_output"
          drive_url="$(
            node -e '
const text = process.argv[1] || "";
const positions = [];
for (let i = 0; i < text.length; i += 1) {
  if (text[i] === "{") positions.push(i);
}
for (const pos of positions.reverse()) {
  try {
    const data = JSON.parse(text.slice(pos));
    const url = data?.data?.url;
    if (url) {
      console.log(url);
      process.exit(0);
    }
  } catch {}
}
process.exit(1);
' "$upload_output"
          )" || drive_url=""
          if [[ -n "$drive_url" ]]; then
            link_text="投研报告 PDF 已上传：$drive_url"
            printf "Drive URL parsed: <%s>\n" "$drive_url"
            lark-cli im +messages-send \
              --chat-id "$notify_chat_id" \
              --text "$link_text" \
              --as "$notify_as"
            echo "sent Drive PDF link for: $rel_file"
          else
            echo "Drive upload succeeded but URL was not found for: $rel_file" >&2
            file_send_failed=1
          fi
        else
          printf "%s\n" "$upload_output" >&2
          echo "Drive upload fallback failed: $rel_file" >&2
          file_send_failed=1
        fi
      else
        file_send_failed=1
      fi
    fi
  done <<< "$notification_files"
  exit "$file_send_failed"
fi
