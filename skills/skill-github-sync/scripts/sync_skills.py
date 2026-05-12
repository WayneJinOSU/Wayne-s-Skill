#!/usr/bin/env python3
"""Sync local Codex skills into a GitHub skills repository."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_REPO = Path(
    "/Users/a/Documents/Codex/2026-04-24/skill-skill-1-4-8-17/Wayne-s-Skill-ssh"
)
DEFAULT_SOURCE = Path.home() / ".codex" / "skills"
SKIP_NAMES = {".system", "codex-primary-runtime"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"ghp_[A-Za-z0-9_]+"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def is_active_skill(path: Path) -> bool:
    if not path.is_dir():
        return False
    if path.name in SKIP_NAMES or path.name.startswith("."):
        return False
    if path.name.endswith(".bak") or ".bak-" in path.name:
        return False
    return (path / "SKILL.md").is_file()


def parse_description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    if not match:
        return "Codex skill."
    return match.group(1).strip().strip('"').strip("'")


def list_skills(source: Path, requested: list[str] | None) -> list[Path]:
    if requested:
        skills = [source / name for name in requested]
        missing = [path.name for path in skills if not is_active_skill(path)]
        if missing:
            raise SystemExit(f"Missing or inactive skill(s): {', '.join(missing)}")
        return skills
    return sorted(path for path in source.iterdir() if is_active_skill(path))


def sync_skill(src: Path, dest_root: Path, dry_run: bool) -> None:
    dest = dest_root / src.name
    if dry_run:
        print(f"Would sync {src} -> {dest}")
        return
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"),
    )


def update_readme(repo: Path, skills: list[Path], dry_run: bool) -> None:
    readme = repo / "README.md"
    entries = []
    for skill in sorted(skills, key=lambda item: item.name):
        desc = parse_description(skill / "SKILL.md")
        entries.append(f"- `{skill.name}`: {desc}")

    content = "\n".join(
        [
            "# Wayne's Skill",
            "",
            "Personal Codex skills maintained as versioned assets.",
            "",
            "## Skills",
            "",
            *entries,
            "",
            "## 如何调用技能",
            "",
            "在 Codex 里可以直接写技能名，再说明研究对象、输出要求，以及是否启动 subagent。也可以不写技能名，只用自然语言描述任务目标；Codex 会根据意图匹配合适的技能。显式写技能名更精准，自然语言调用更顺手。",
            "",
            "调用方式：",
            "",
            "1. 点名技能调用：",
            "",
            "研究主控：",
            "",
            "- `equity-catalyst-tracker 调研东山精密，启动 subagent`",
            "- `industry-chain-agentic-research 研究AI服务器产业链，启动 subagent，拆分上游材料、PCB、连接器、电源、液冷和整机环节`",
            "- `chassis-growth-agentic-research 研究东山精密，重点看旧业务底盘、第二成长曲线和估值透支`",
            "- `supply-chain-agentic-research 调研工业富联，启动 subagent，输出正式深度报告`",
            "- `local-bank-research 研究江苏银行，重点拆利润桥、资产质量、区域beta、分红和估值预期差`",
            "",
            "底盘成长模块：",
            "",
            "- `chassis-growth-base-business 分析东山精密旧业务底盘，看收入利润、现金流、客户基础和估值下限`",
            "- `chassis-growth-second-curve 分析东山精密第二成长曲线，看AI算力PCB是否抬高收入、利润率和估值身份`",
            "- `chassis-growth-platform-reuse 分析东山精密平台复用能力，看客户、工艺、产能和认证体系是否能迁移到新业务`",
            "",
            "供应链模块：",
            "",
            "- `supply-chain-cycle-capex 分析AI服务器产业周期，重点看云厂商capex、产品迭代和周期见顶风险`",
            "- `supply-chain-position-moat 分析工业富联供应链地位，看客户认证、规模交付、全球产能和可替代性`",
            "- `supply-chain-orders-shipments 分析沪电股份订单出货，看排产、库存、应收、合同负债和收入确认`",
            "",
            "公共成长模块：",
            "",
            "- `common-growth-execution-signals 跟踪东山精密承接动作，看扩产、设备、客户验证、订单和量产节点`",
            "- `common-growth-profit-bridge 拆东山精密利润桥，分存量利润、新业务新增利润和扩张成本，做三种情景`",
            "- `common-growth-forward-valuation 反推东山精密当前市值隐含利润，看估值反映到哪一年、是否透支`",
            "",
            "数据、写作和工具类：",
            "",
            "- `akshare 获取东山精密近一年行情、估值和财务数据，并做简要趋势分析`",
            "- `tushare 导出东山精密近三年财务指标、估值和日行情，整理成表格`",
            "- `wencai-query 查询最近10日涨停次数最多的A股，导出表格`",
            "- `finance-research-xhs 把东山精密研究报告改写成小红书长文本笔记`",
            "- `frontend-design 做一个AI算力供应链研究仪表盘，包含公司对比、催化事件和风险提示`",
            "- `doc 把东山精密研究报告整理成docx，保留标题层级、表格和风险提示`",
            "- `find-skills 找一个适合做A股公告跟踪和财报解析的skill`",
            "- `skill-github-sync 重新同步本地skills到GitHub仓库，并更新README`",
            "",
            "2. 不点名技能的自然语言调用：",
            "",
            "研究主控：",
            "",
            "- `调研东山精密，重点看4月9日前后是否有订单、客户、财报或市场行为催化；启动 subagent，输出证据链和后续跟踪清单`",
            "- `研究AI服务器产业链，启动 subagent，拆分上游材料、PCB、连接器、电源、液冷和整机环节，输出完整产业链深度报告`",
            "- `研究东山精密，重点看旧业务底盘、第二成长曲线、平台复用能力、利润桥和估值是否透支`",
            "- `调研工业富联，启动 subagent，重点看AI服务器订单、客户结构、供应链地位、利润释放和远期估值`",
            "- `研究江苏银行，重点拆利润桥、资产质量、区域beta、债券投资、分红和估值预期差`",
            "",
            "底盘成长模块：",
            "",
            "- `分析东山精密旧业务底盘，看收入利润、现金流、客户基础、行业地位和估值下限`",
            "- `分析东山精密第二成长曲线，看AI算力PCB是否抬高收入、利润率、成长天花板和估值身份`",
            "- `分析东山精密平台复用能力，看客户、工艺、产能、供应链和认证体系是否能迁移到新业务`",
            "",
            "供应链模块：",
            "",
            "- `分析AI服务器产业周期，重点看云厂商capex、下游需求持续性、产品迭代和周期见顶风险`",
            "- `分析工业富联供应链地位，看客户认证、规模交付、复杂产品量产、全球产能和可替代性`",
            "- `分析沪电股份订单出货，看排产、库存、应收、合同负债、收入确认和经营现金流质量`",
            "",
            "公共成长模块：",
            "",
            "- `跟踪东山精密承接动作，看扩产、融资、设备、客户验证、订单、量产和海外基地进展`",
            "- `拆东山精密利润桥，分存量利润、新业务新增利润和扩张成本，做保守、中性、乐观三种情景`",
            "- `反推东山精密当前市值隐含利润，看估值反映到哪一年、是否透支、关键证伪点是什么`",
            "",
            "数据、写作和工具类：",
            "",
            "- `获取东山精密近一年行情、估值和财务数据，并做简要趋势分析`",
            "- `导出东山精密近三年财务指标、估值和日行情，整理成表格`",
            "- `查询最近10日涨停次数最多的A股，导出表格`",
            "- `把东山精密研究报告改写成小红书长文本笔记，保留证据链、风险和假设分层`",
            "- `做一个AI算力供应链研究仪表盘，包含公司对比、催化事件、估值和风险提示`",
            "- `把东山精密研究报告整理成docx，保留标题层级、表格和风险提示`",
            "- `帮我找一个适合做A股公告跟踪和财报解析的skill`",
            "- `重新同步我的本地skills仓库，并更新GitHub仓库README`",
            "",
            "## Local install",
            "",
            "Install or update all skills from this repo into Codex:",
            "",
            "```bash",
            "mkdir -p ~/.codex/skills",
            "cp -R skills/* ~/.codex/skills/",
            "```",
            "",
            "Restart Codex after installing or updating skills.",
            "",
        ]
    )
    if dry_run:
        print(f"Would update {readme}")
        return
    readme.write_text(content, encoding="utf-8")


def scan_for_secrets(repo: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted((repo / "skills").rglob("*")):
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line_no = text[: match.start()].count("\n") + 1
                findings.append(f"{path.relative_to(repo)}:{line_no}: {match.group(0)[:80]}")
    return findings


def ensure_repo(repo: Path) -> None:
    if not (repo / ".git").is_dir():
        raise SystemExit(f"Not a git repository: {repo}")
    if not (repo / "skills").exists():
        (repo / "skills").mkdir(parents=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(os.environ.get("WAYNE_SKILL_REPO", DEFAULT_REPO)))
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--skill", action="append", help="Skill name to sync. Repeat to sync multiple.")
    parser.add_argument("--commit", action="store_true", help="Create a git commit after syncing.")
    parser.add_argument("--push", action="store_true", help="Push to the configured git remote after commit.")
    parser.add_argument("--prune", action="store_true", help="Delete repo skills not present in the selected local set.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing files.")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    source = args.source.expanduser().resolve()
    ensure_repo(repo)
    selected = list_skills(source, args.skill)
    dest_root = repo / "skills"

    selected_names = {path.name for path in selected}
    if args.prune and not args.dry_run:
        for existing in dest_root.iterdir():
            if existing.is_dir() and existing.name not in selected_names:
                shutil.rmtree(existing)

    for skill in selected:
        sync_skill(skill, dest_root, args.dry_run)
    repo_skills = sorted(path for path in dest_root.iterdir() if is_active_skill(path))
    update_readme(repo, repo_skills if not args.dry_run else selected, args.dry_run)

    if args.dry_run:
        return 0

    findings = scan_for_secrets(repo)
    if findings:
        print("Potential secret patterns found. Review before committing:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 2

    status = run(["git", "status", "--short"], cwd=repo).stdout.strip()
    if not status:
        print("No changes to commit.")
        return 0

    print(status)
    if args.commit:
        names = ", ".join(sorted(selected_names))
        run(["git", "add", "README.md", "skills"], cwd=repo)
        run(["git", "commit", "-m", f"Sync Codex skills: {names}"], cwd=repo)
        if args.push:
            run(["git", "push", "origin", "main"], cwd=repo)
    elif args.push:
        raise SystemExit("--push requires --commit")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
