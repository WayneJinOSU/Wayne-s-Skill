#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GLOBAL_SKILLS_DIR="${GLOBAL_SKILLS_DIR:-$HOME/.codex/skills}"
PROJECT_SKILLS_DIR="${PROJECT_SKILLS_DIR:-$ROOT_DIR/.agents/skills}"
PROJECTS_ROOT="${PROJECTS_ROOT:-/Users/a/PycharmProjects}"
SCAN_MODE="current"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all-projects)
      SCAN_MODE="all"
      shift
      ;;
    --projects-root)
      if [[ $# -lt 2 ]]; then
        echo "--projects-root requires a value" >&2
        exit 1
      fi
      PROJECTS_ROOT="$2"
      shift 2
      ;;
    --project-skills-dir)
      if [[ $# -lt 2 ]]; then
        echo "--project-skills-dir requires a value" >&2
        exit 1
      fi
      PROJECT_SKILLS_DIR="$2"
      shift 2
      ;;
    --global-skills-dir)
      if [[ $# -lt 2 ]]; then
        echo "--global-skills-dir requires a value" >&2
        exit 1
      fi
      GLOBAL_SKILLS_DIR="$2"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: scripts/check_skill_drift.sh [--all-projects] [--projects-root DIR] [--project-skills-dir DIR] [--global-skills-dir DIR]

Checks whether project-level skills with the same SKILL.md name as a user-level global skill have drifted.

Defaults:
  project skills: $PWD/.agents/skills
  global skills : $HOME/.codex/skills

Options:
  --all-projects        scan all .agents/skills directories under /Users/a/PycharmProjects
  --projects-root DIR   root used by --all-projects
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

node - "$GLOBAL_SKILLS_DIR" "$PROJECT_SKILLS_DIR" "$PROJECTS_ROOT" "$SCAN_MODE" <<'NODE'
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const [globalRoot, projectSkillsDir, projectsRoot, scanMode] = process.argv.slice(2);
const skipDirs = new Set([
  ".git",
  ".venv",
  "venv",
  "node_modules",
  "__pycache__",
  ".mypy_cache",
  ".pytest_cache",
  ".ruff_cache",
  ".codex_research",
]);

function walk(dir, predicate, depth = 0, maxDepth = 10) {
  const out = [];
  if (depth > maxDepth) return out;
  let entries = [];
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  entries.sort((a, b) => a.name.localeCompare(b.name));
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!skipDirs.has(entry.name)) {
        out.push(...walk(full, predicate, depth + 1, maxDepth));
      }
    } else if (entry.isFile() && predicate(full)) {
      out.push(full);
    }
  }
  return out;
}

function stripQuotes(value) {
  return value.trim().replace(/^['"]|['"]$/g, "");
}

function readSkillName(skillFile) {
  const text = fs.readFileSync(skillFile, "utf8");
  const frontMatter = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (frontMatter) {
    for (const rawLine of frontMatter[1].split(/\r?\n/)) {
      const line = rawLine.trim();
      const match = line.match(/^name:\s*(.+)$/);
      if (match) return stripQuotes(match[1]);
    }
  }
  return path.basename(path.dirname(skillFile));
}

function shaFile(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function listDirFiles(dir) {
  return walk(dir, () => true, 0, 8).filter((file) => !file.endsWith(`${path.sep}.DS_Store`));
}

function dirDigest(dir) {
  const h = crypto.createHash("sha256");
  for (const file of listDirFiles(dir)) {
    const rel = path.relative(dir, file).split(path.sep).join("/");
    h.update(rel);
    h.update("\0");
    h.update(fs.readFileSync(file));
    h.update("\0");
  }
  return h.digest("hex");
}

function readSkills(root, maxDepth = 4) {
  const map = new Map();
  const files = walk(root, (file) => path.basename(file) === "SKILL.md", 0, maxDepth);
  for (const file of files) {
    const dir = path.dirname(file);
    const name = readSkillName(file);
    map.set(name, {
      name,
      dir,
      skillFile: file,
      skillDigest: shaFile(file),
      dirDigest: dirDigest(dir),
    });
  }
  return map;
}

function findProjectSkillFiles() {
  if (scanMode === "all") {
    return walk(
      projectsRoot,
      (file) => file.endsWith(`${path.sep}SKILL.md`) && file.includes(`${path.sep}.agents${path.sep}skills${path.sep}`),
      0,
      10
    );
  }
  return walk(projectSkillsDir, (file) => path.basename(file) === "SKILL.md", 0, 4);
}

const globalSkills = readSkills(globalRoot);
const projectSkillFiles = findProjectSkillFiles();
const duplicates = [];

for (const file of projectSkillFiles) {
  const name = readSkillName(file);
  const globalSkill = globalSkills.get(name);
  if (!globalSkill) continue;
  const projectDir = path.dirname(file);
  duplicates.push({
    name,
    projectDir,
    globalDir: globalSkill.dir,
    skillSame: shaFile(file) === globalSkill.skillDigest,
    dirSame: dirDigest(projectDir) === globalSkill.dirDigest,
  });
}

duplicates.sort((a, b) => `${a.projectDir}:${a.name}`.localeCompare(`${b.projectDir}:${b.name}`));

console.log(`scan_mode=${scanMode}`);
console.log(`global_skills=${globalSkills.size} root=${globalRoot}`);
console.log(`project_skill_files_scanned=${projectSkillFiles.length}`);
console.log(`duplicates_with_global=${duplicates.length}`);

let driftCount = 0;
for (const item of duplicates) {
  const ok = item.skillSame && item.dirSame;
  if (!ok) driftCount += 1;
  console.log(`${ok ? "[OK]" : "[DRIFT]"} ${item.name}`);
  console.log(`  project: ${item.projectDir}`);
  console.log(`  global : ${item.globalDir}`);
  console.log(`  SKILL.md: ${item.skillSame ? "same" : "DIFF"}`);
  console.log(`  full dir: ${item.dirSame ? "same" : "DIFF"}`);
}

if (driftCount > 0) {
  console.error(`duplicate skill drift detected: ${driftCount}`);
  process.exit(1);
}

console.log("No duplicate skill drift detected.");
NODE
