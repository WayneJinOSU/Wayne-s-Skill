#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export GIT_CEILING_DIRECTORIES="${GIT_CEILING_DIRECTORIES:-$(dirname "$ROOT_DIR")}"
CODEX_BIN="${CODEX_BIN:-/Applications/Codex.app/Contents/Resources/codex}"
TASKS_DIR="${TASKS_DIR:-$ROOT_DIR/tasks}"
MAX_TASKS="${MAX_TASKS:-0}"
MODEL="${MODEL:-}"
SANDBOX="${SANDBOX:-danger-full-access}"
TASK_TIMEOUT_SECONDS="${RESEARCH_TASK_TIMEOUT_SECONDS:-7200}"

write_output_manifest() {
  local task_dir="$1"
  local status="$2"
  local selected_skill="$3"
  local finished_at="$4"

  node - "$task_dir" "$status" "$selected_skill" "$finished_at" <<'NODE'
const fs = require("node:fs");
const path = require("node:path");

const [taskDir, status, selectedSkill, finishedAt] = process.argv.slice(2);

function exists(file) {
  return fs.existsSync(file);
}

function walk(dir) {
  if (!exists(dir)) return [];
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else if (entry.isFile()) out.push(full);
  }
  return out;
}

function rel(file) {
  return path.relative(taskDir, file).split(path.sep).join("/");
}

const artifactsDir = path.join(taskDir, "research_artifacts");
const artifactFiles = walk(artifactsDir).map(rel).sort();
const coreOutputs = artifactFiles.filter((file) => (
  /(_final_report|_final_report_full|_integrated_update|_valuation_deepdive|_valuation_scorecard|_valuation_handoff|_tracking_dashboard|_skeptic_review)\.md$/i.test(file)
));
const sourceArtifactRe = /(?:^|\/)(sources?|source_pdfs?|source_texts?)(?:\/|$)/i;
const pdfOutputs = artifactFiles.filter((file) => /\.pdf$/i.test(file) && !sourceArtifactRe.test(file));

const manifest = {
  status,
  task_dir: taskDir,
  selected_skill: selectedSkill,
  final_message: exists(path.join(taskDir, "final_message.txt")) ? "final_message.txt" : "",
  artifact_root: "research_artifacts",
  core_outputs: coreOutputs,
  pdf_outputs: pdfOutputs,
  artifact_files: artifactFiles,
  finished_at: finishedAt,
};

fs.writeFileSync(path.join(taskDir, "output_manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
NODE
}

notify_task_result() {
  local task_dir="$1"
  if [[ -f "$task_dir/notify.json" && -x "$ROOT_DIR/scripts/notify_research_result.sh" ]]; then
    "$ROOT_DIR/scripts/notify_research_result.sh" "$task_dir" >> "$task_dir/notify.log" 2>&1 || {
      echo "[$(basename "$task_dir")] notification failed; see $task_dir/notify.log" >&2
    }
  fi
}

normalize_skill() {
  local raw
  raw="$(printf "%s" "${1:-auto}" | tr '[:upper:]' '[:lower:]' | tr -d '`[:space:]')"
  case "$raw" in
    auto|"") printf "auto\n" ;;
    supply|supply-chain|supply-chain-agentic|supply-chain-agentic-research|供应链|供应链平台)
      printf "supply-chain-agentic-research\n"
      ;;
    chassis|chassis-growth|chassis-growth-agentic|chassis-growth-agentic-research|成长股|底盘|底盘成长)
      printf "chassis-growth-agentic-research\n"
      ;;
    catalyst|tracker|equity-catalyst|equity-catalyst-tracker|爆点|跟踪|催化)
      printf "equity-catalyst-tracker\n"
      ;;
    valuation|growth-stock-valuation|估值|peg)
      printf "growth-stock-valuation\n"
      ;;
    xhs|redbook|xiaohongshu|finance-research-xhs|小红书|小红书写作|投研小红书|笔记|长文笔记)
      printf "finance-research-xhs\n"
      ;;
    industry|industry-chain|industry-chain-agentic|industry-chain-agentic-research|行业|产业链)
      printf "industry-chain-agentic-research\n"
      ;;
    *)
      printf "%s\n" "$raw"
      ;;
  esac
}

select_skill() {
  local task_dir="$1"
  local brief="$2"
  local override="auto"

  if [[ -f "$task_dir/skill" ]]; then
    override="$(normalize_skill "$(head -n 1 "$task_dir/skill")")"
    if [[ "$override" != "auto" ]]; then
      printf "%s\n" "$override"
      return
    fi
  fi

  override="$(awk -F '[:：]' '/推荐 skill|recommended[ _-]?skill/i {gsub(/^[ \t-]+|[ \t]+$/, "", $2); print $2; exit}' "$brief")"
  override="$(normalize_skill "${override:-auto}")"

  if [[ "$override" != "auto" ]]; then
    printf "%s\n" "$override"
    return
  fi

  if grep -Eiq '小红书|XHS|xiaohongshu|redbook|投研笔记|股票分析笔记|长文本笔记|长文笔记|非种草|非带货' "$brief"; then
    printf "finance-research-xhs\n"
  elif grep -Eiq '估值|目标市值|目标价|PEG|PE|赔率|隐含利润|估值锚|贵不贵' "$brief"; then
    printf "growth-stock-valuation\n"
  elif grep -Eiq '爆点|催化|持续跟踪|跟踪.*公告|跟踪.*订单|最新|刚发布|右侧确认|高潮|退潮|证伪.*事件' "$brief"; then
    printf "equity-catalyst-tracker\n"
  elif grep -Eiq '行业深度|产业链深度|产业链研究|赛道|细分环节|产业链全景|行业格局' "$brief"; then
    printf "industry-chain-agentic-research\n"
  elif grep -Eiq '底盘|旧业务|第二曲线|第二成长曲线|平台复用|行业经济性|蛋糕分配|份额提升' "$brief"; then
    printf "chassis-growth-agentic-research\n"
  elif grep -Eiq '供应链|AI算力|数据中心|新能源|机器人|先进封装|半导体|半导体材料|电子材料|设备|价值量|客户认证|订单出货|产能升级|利润天花板' "$brief"; then
    printf "supply-chain-agentic-research\n"
  else
    printf "chassis-growth-agentic-research\n"
  fi
}

skill_roots_context() {
  node - "$ROOT_DIR" <<'NODE'
const fs = require("node:fs");
const path = require("node:path");

const rootDir = process.argv[2];
const home = process.env.HOME || "";
const defaultRoots = [
  path.join(rootDir, ".agents", "skills"),
  home ? path.join(home, ".codex", "skills") : "",
].filter(Boolean);

function splitRoots(value) {
  return String(value || "")
    .split(path.delimiter)
    .map((item) => item.trim())
    .filter(Boolean);
}

const configuredRoots = splitRoots(process.env.RESEARCH_SKILL_ROOTS || "");
const extraRoots = splitRoots(process.env.RESEARCH_EXTRA_SKILL_ROOTS || "");
const roots = [];
for (const candidate of [...(configuredRoots.length ? configuredRoots : defaultRoots), ...extraRoots]) {
  const resolved = path.resolve(candidate);
  if (!roots.includes(resolved)) roots.push(resolved);
}

function findSkillFiles(root) {
  const out = [];
  function visit(dir, depth) {
    if (depth > 4) return;
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    entries.sort((a, b) => a.name.localeCompare(b.name));
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isFile() && entry.name === "SKILL.md") {
        out.push(full);
      } else if (entry.isDirectory() && !["node_modules", ".git", ".codex_research"].includes(entry.name)) {
        visit(full, depth + 1);
      }
    }
  }
  visit(root, 0);
  return out;
}

function stripQuotes(value) {
  return value.trim().replace(/^['"]|['"]$/g, "");
}

function readSkillMeta(file) {
  const text = fs.readFileSync(file, "utf8");
  const frontMatter = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  let name = path.basename(path.dirname(file));
  let description = "";
  if (frontMatter) {
    for (const rawLine of frontMatter[1].split(/\r?\n/)) {
      const line = rawLine.trim();
      const nameMatch = line.match(/^name:\s*(.+)$/);
      const descriptionMatch = line.match(/^description:\s*(.+)$/);
      if (nameMatch) name = stripQuotes(nameMatch[1]);
      if (descriptionMatch) description = stripQuotes(descriptionMatch[1]);
    }
  }
  description = description.replace(/\s+/g, " ").trim();
  if (description.length > 180) description = `${description.slice(0, 177)}...`;
  return { name, description };
}

const lines = [
  "- Skill roots（按优先级合并；同名 skill 以前面的 root 为准）：",
];

for (const root of roots) {
  lines.push(`  - \`${root}\`${fs.existsSync(root) ? "" : "（不存在）"}`);
}

const seen = new Set();
const skills = [];
for (const root of roots) {
  for (const file of findSkillFiles(root)) {
    const meta = readSkillMeta(file);
    if (seen.has(meta.name)) continue;
    seen.add(meta.name);
    skills.push({ ...meta, file });
  }
}

if (skills.length === 0) {
  lines.push("- 未在上述 roots 发现 `SKILL.md`；如需 skill，先检查 `RESEARCH_SKILL_ROOTS` 或目录权限。");
} else {
  lines.push("- 已发现 skills（去重后）：");
  for (const skill of skills) {
    const suffix = skill.description ? ` — ${skill.description}` : "";
    lines.push(`  - \`${skill.name}\` @ \`${skill.file}\`${suffix}`);
  }
}

console.log(lines.join("\n"));
NODE
}

core_outputs_for_skill() {
  local skill="$1"
  case "$skill" in
    supply-chain-agentic-research)
      cat <<'EOF'
	- 核心终点文件：`research_artifacts/<标的>/<标的>_final_report.md`
	- 关键配套文件：`research_artifacts/<标的>/<标的>_valuation_handoff.md`、`research_artifacts/<标的>/<标的>_tracking_dashboard.md`、`research_artifacts/<标的>/<标的>_skeptic_review.md`
	- 若进入估值接力，再生成 `<标的>_valuation_deepdive.md` 和 `<标的>_valuation_scorecard.md`
EOF
      ;;
    chassis-growth-agentic-research)
      cat <<'EOF'
	- 核心终点文件：`research_artifacts/<标的>/<标的>_final_report.md`
	- 关键配套文件：`research_artifacts/<标的>/<标的>_valuation_handoff.md`、`research_artifacts/<标的>/<标的>_tracking_dashboard.md`、`research_artifacts/<标的>/<标的>_skeptic_review.md`
EOF
      ;;
    equity-catalyst-tracker)
      cat <<'EOF'
	- 核心终点文件：`research_artifacts/<标的>/<标的>_integrated_update.md`
	- 关键配套文件：`research_artifacts/<标的>/<标的>_baseline_card.md`、`research_artifacts/<标的>/<标的>_catalyst_log.md`、`research_artifacts/<标的>/<标的>_stage_scorecard.md`、`research_artifacts/<标的>/<标的>_watchlist.md`、`research_artifacts/<标的>/<标的>_agent_findings.md`
EOF
      ;;
    growth-stock-valuation)
      cat <<'EOF'
	- 核心终点文件：`research_artifacts/<标的>/<标的>_valuation_deepdive.md`
	- 关键配套文件：`research_artifacts/<标的>/<标的>_catalyst_precheck.md`（或已有 `<标的>_integrated_update.md`）、`research_artifacts/<标的>/<标的>_valuation_scorecard.md`
EOF
      ;;
    finance-research-xhs)
      cat <<'EOF'
	- 核心终点文件：`research_artifacts/<标的或主题>/<标的或主题>_xhs_note.md`
	- 若内容过长或多业务线，生成 `research_artifacts/<标的或主题>/<标的或主题>_xhs_series_plan.md`
	- 必须保留事实/推断/假设/个人判断分层、风险和后续跟踪指标
EOF
      ;;
    industry-chain-agentic-research)
      cat <<'EOF'
	- 核心终点文件：`research_artifacts/<行业或主线>/<prefix>_final_report_full.md`
	- 关键配套文件：`research_artifacts/<行业或主线>/<prefix>_executive_summary.md`、`research_artifacts/<行业或主线>/<prefix>_plain_investor_guide.md`、`research_artifacts/<行业或主线>/<prefix>_report_synthesis.md`、`research_artifacts/<行业或主线>/<prefix>_editorial_thesis.md`
EOF
      ;;
    *)
      cat <<'EOF'
- 核心终点文件：按所选 skill 的 SKILL.md 原生主终点文件命名
- 关键配套文件：按该 skill 的 Workflow / Output 约定生成
EOF
      ;;
  esac
}

peg_valuation_rules_for_skill() {
  local skill="$1"
  if [[ "$skill" != "growth-stock-valuation" ]]; then
    return 0
  fi

  cat <<'EOF'

PEG 估值前置规则（仅适用于 `growth-stock-valuation`，不改变 DCF 或其他 skill）：
- 在生成 `<标的>_valuation_deepdive.md` / `<标的>_valuation_scorecard.md` 前，必须先显式执行一次 `$equity-catalyst-tracker` 子流程，聚焦最近公告、订单、财报、股价异动、产业新闻和未来 1-3 个月催化。
- 若当前环境无法真正嵌套调用 skill，必须按 `equity-catalyst-tracker` 的核心结构生成或刷新前置产物：`research_artifacts/<标的>/<标的>_catalyst_precheck.md`（或已有 `<标的>_integrated_update.md`），至少包含 catalyst log、stage scorecard、watchlist、红黄绿灯和证伪条件。
- PEG 估值主体必须分成三视角：
  1. Auditor View：只按已披露/审计/公告和财报口径，判断底线、风险、现金流和证伪条件；不得用它单独替代最终估值。
  2. PM View：按市场正在交易的未来 12-24 个月利润、一致预期/自有利润桥和同行估值，判断当前贵不贵和合理 PEG/PE 区间。
  3. Catalyst View：承接前置 catalyst 检查，说明哪些关键催化兑现后允许 PEG 系数上修或年份切到更远期；哪些未兑现必须锁回 Auditor/PM 基准。
- `<标的>_valuation_scorecard.md` 必须同时列示三视角结论、权重/优先级、当前估值所在区间和触发/证伪条件。
- 禁止把“审计口径”作为唯一估值结论；禁止把未验证催化直接资本化为基准情景；催化只能通过明确条件进入乐观情景或年份切换。
EOF
}

if [[ ! -x "$CODEX_BIN" ]]; then
  echo "Codex CLI not found or not executable: $CODEX_BIN" >&2
  exit 1
fi

if [[ ! -d "$TASKS_DIR" ]]; then
  echo "Tasks directory not found: $TASKS_DIR" >&2
  exit 1
fi

count=0

while IFS= read -r status_file; do
  task_dir="$(dirname "$status_file")"
  task_name="$(basename "$task_dir")"
  brief="$task_dir/brief.md"
  log="$task_dir/run.log"
  prompt="$task_dir/prompt.md"

  if [[ "$task_name" == "_template" ]]; then
    continue
  fi

  if [[ ! -f "$brief" ]]; then
    echo "[$task_name] missing brief.md; marking failed" >&2
    printf "failed\n" > "$status_file"
    continue
  fi

  selected_skill="$(select_skill "$task_dir" "$brief")"
  core_outputs="$(core_outputs_for_skill "$selected_skill")"
  peg_valuation_rules="$(peg_valuation_rules_for_skill "$selected_skill")"
  skill_roots_context="$(skill_roots_context)"

  if [[ "$selected_skill" == "auto" ]]; then
    skill_execution_rules="$(cat <<'EOF'
- 本任务未由桥接脚本预选主 skill；你必须根据 brief 中的用户原始指令，在当前 Codex 可用 skills 中自行选择并显式使用最合适的 skill。
- 如果用户要求“选择合适的 skill”，不要让脚本关键词替你做决定；由你阅读原始指令后判断。
- 个股深度投研通常优先在 `$supply-chain-agentic-research`、`$chassis-growth-agentic-research`、`$growth-stock-valuation`、`$equity-catalyst-tracker`、`$industry-chain-agentic-research` 中选择；投研内容改写/小红书长文优先用 `$finance-research-xhs`；若原始指令更匹配其他 skill，以原始指令为准。
- 在 `research_artifacts/subagent_plan.md` 中记录你最终选择的 skill 和理由。
EOF
)"
  else
    skill_trigger="\$$selected_skill"
    skill_execution_rules="$(cat <<EOF
- 本任务已选择主 skill：\`$selected_skill\`。
- 你必须使用 \`$skill_trigger\`，并遵循该 skill 的正式工作流、Agent Policy、Non-negotiables 和输出约束。
EOF
)"
  fi

  if [[ "$MAX_TASKS" != "0" && "$count" -ge "$MAX_TASKS" ]]; then
    break
  fi

  count=$((count + 1))
  started_at="$(date '+%Y-%m-%d %H:%M:%S %z')"
  printf "running\n" > "$status_file"
  printf "%s\n" "$started_at" > "$task_dir/started_at"
  printf "%s\n" "$selected_skill" > "$task_dir/selected_skill"
  printf "%s\n" "$core_outputs" > "$task_dir/expected_core_outputs"

  cat > "$prompt" <<PROMPT
你正在执行一个自动化投研队列中的单个任务。

硬性隔离规则：
- 只把下面 brief 视为本任务上下文。
- 不要继承其他任务、其他窗口、其他报告的结论。
- 默认工作目录是本任务目录：$task_dir
- 不要生成统一的 \`output.md\` 作为主交付。
- 最终交付必须使用所选 skill 的原生核心文件命名，并写入本任务目录下的 \`research_artifacts/\`。
- 如需读取材料，优先读取本任务目录下的文件；只有 brief 明确列出的外部路径可以使用。
- 完成后，在最终回复中简要说明写入了哪些文件。

研究执行规则：
- Skill 发现必须合并用户级全局 skills 与项目级 skills；不要只扫描当前项目 `.agents/skills`。通用跨项目 skill 默认在 `$HOME/.codex/skills`，项目专属桥接/飞书流程默认在本仓库 `.agents/skills`。
$skill_roots_context
- 执行某个 skill 前，如果当前 Codex 运行环境没有直接注入该 skill 的说明，必须从上面列出的对应 `SKILL.md` 路径读取完整说明后再行动。
- 用户明确要求本自动化任务调用合适的 skill；是否启动 subagent 以 brief 中的用户原始指令为准。
$skill_execution_rules
$peg_valuation_rules
- 如果 brief 明确禁止启动 subagent / multi-agent，则不得启动真实 subagent；改用分阶段文件化方式完成同等角色研究，并在 \`research_artifacts/subagent_plan.md\` 说明“用户禁止启动 subagent”。
- 如果 brief 没有禁止 subagent，且当前环境提供 subagent / multi-agent 工具，必须按该 skill 的角色分工启动真实 subagent；不要把多角色研究压缩成一次性摘要。
- 如需启动 subagent，启动前先写一个简短分工计划到 \`research_artifacts/subagent_plan.md\`；每个 subagent 的任务必须具体、互不重复，并要求其把发现写入 \`research_artifacts/\` 下的对应文件。
- 如果当前环境确实不能启动真实 subagent，必须在 \`research_artifacts/subagent_plan.md\` 说明原因，并用分阶段文件化方式模拟同样角色；不得跳过中间产物、QA、反方审查或证据边界。
- 不允许直接生成终稿。必须先形成中间研究产物，再整合生成所选 skill 的核心终点文件。

本任务预期核心输出：
$core_outputs

命名规则：
- 若 brief 中给出股票代码或公司简称，优先用它作为 \`<标的>\`。
- 若 brief 中没有明确标的，先在 \`research_artifacts/subagent_plan.md\` 中定义一个稳定短前缀，再用该前缀命名全部核心文件。
- 不要把所有内容压缩到一个通用摘要文件；保留 skill 要求的中间文件、QA 文件和主终点文件。

下面是 brief：

$(cat "$brief")
PROMPT

  echo "[$task_name] started at $started_at with skill $selected_skill"

  codex_args=(
    exec
    --cd "$task_dir"
    --skip-git-repo-check
    --sandbox "$SANDBOX"
    --output-last-message "$task_dir/final_message.txt"
  )

  if [[ -n "$MODEL" ]]; then
    codex_args+=(--model "$MODEL")
  fi

  timed_out=false
  set +e
  "$CODEX_BIN" "${codex_args[@]}" - < "$prompt" > "$log" 2>&1 &
  codex_pid="$!"
  started_epoch="$(date +%s)"

  while kill -0 "$codex_pid" 2>/dev/null; do
    if [[ "$TASK_TIMEOUT_SECONDS" != "0" ]]; then
      now_epoch="$(date +%s)"
      if (( now_epoch - started_epoch >= TASK_TIMEOUT_SECONDS )); then
        timed_out=true
        {
          echo ""
          echo "[$(date '+%Y-%m-%d %H:%M:%S %z')] task timed out after ${TASK_TIMEOUT_SECONDS}s; terminating codex process pid=$codex_pid"
        } >> "$log"
        kill -TERM "$codex_pid" 2>/dev/null || true
        sleep 10
        kill -KILL "$codex_pid" 2>/dev/null || true
        break
      fi
    fi
    sleep 5
  done

  wait "$codex_pid"
  exit_code=$?
  set -e

  if [[ "$timed_out" == true ]]; then
    exit_code=124
    printf "%s\n" "$TASK_TIMEOUT_SECONDS" > "$task_dir/timeout_seconds"
  fi

  finished_at="$(date '+%Y-%m-%d %H:%M:%S %z')"
  printf "%s\n" "$finished_at" > "$task_dir/finished_at"
  printf "%s\n" "$exit_code" > "$task_dir/exit_code"

  if [[ "$exit_code" -eq 0 ]]; then
    printf "done\n" > "$status_file"
    write_output_manifest "$task_dir" "done" "$selected_skill" "$finished_at"
    notify_task_result "$task_dir"
    echo "[$task_name] done at $finished_at"
  elif [[ "$timed_out" == true ]]; then
    printf "timeout\n" > "$status_file"
    write_output_manifest "$task_dir" "timeout" "$selected_skill" "$finished_at"
    notify_task_result "$task_dir"
    echo "[$task_name] timed out after ${TASK_TIMEOUT_SECONDS}s; see $log" >&2
  else
    printf "failed\n" > "$status_file"
    write_output_manifest "$task_dir" "failed" "$selected_skill" "$finished_at"
    notify_task_result "$task_dir"
    echo "[$task_name] failed with exit code $exit_code; see $log" >&2
  fi
done < <(find "$TASKS_DIR" -mindepth 2 -maxdepth 2 -name status -type f -exec sh -c 'for f do [ "$(tr -d "[:space:]" < "$f")" = queued ] && printf "%s\n" "$f"; done' sh {} + | sort)

if [[ "$count" -eq 0 ]]; then
  echo "No queued tasks found."
fi
