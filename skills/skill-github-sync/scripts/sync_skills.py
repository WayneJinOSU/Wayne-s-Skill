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


def default_readme_tail() -> str:
    return "\n".join(
        [
            "## 估值链路",
            "",
            "正式成长股估值拆成四个独立环节，避免一个 skill 同时承担研究、建模、定价和汇总：",
            "",
            "```text",
            "研究主控",
            "  -> financial-modeling",
            "  -> growth-stock-valuation + dcf-model",
            "  -> integrated-growth-valuation",
            "```",
            "",
            "- `financial-modeling`：把研究主控输出的 `dcf_financial_model_handoff` 转成三表、FCF、PEG-ready 和 DCF-ready 数据包，不输出目标价或最终估值结论。",
            "- `growth-stock-valuation`：只做 PEG / 动态 PE 成长股定价，输出目标市值区间、情景、年份切换和证伪点。",
            "- `dcf-model`：官方 DCF skill，只基于 DCF-ready 现金流输入独立生成 DCF Excel、summary 和 validation。",
            "- `integrated-growth-valuation`：只聚合 `growth-stock-valuation` 和 `dcf-model` 已完成的结果，不重新建模、不平均两个模型、不创造新目标价。",
            "",
            "`dcf-valuation` 已删除；正式 DCF 一律使用 `dcf-model`。",
            "",
            "## 如何调用技能",
            "",
            "在 Codex 里可以直接写技能名，再说明研究对象、输出要求，以及是否启动 subagent。也可以不写技能名，只用自然语言描述任务目标；Codex 会根据意图匹配合适的技能。显式写技能名更精准，自然语言调用更顺手。",
            "",
            "调用方式：",
            "",
            "注意：仓库里的 `modules/`、`references/`、`agents/` 是某些主控 skill 的内部材料，不是独立 skill，也不需要单独点名调用。调用时只点名真实存在的 skill；如果不确定，就用自然语言描述目标，让 Codex 自动匹配。",
            "",
            "1. 点名技能调用：",
            "",
            "研究与跟踪：",
            "",
            "- `equity-catalyst-tracker 调研东山精密，启动 subagent`",
            "- `industry-chain-agentic-research 研究AI服务器产业链，启动 subagent，拆分上游材料、PCB、连接器、电源、液冷和整机环节`",
            "- `chassis-growth-agentic-research 研究东山精密，重点看市场重定价、旧业务底盘、第二成长曲线、竞争客户验证和估值接力输入`",
            "- `supply-chain-agentic-research 调研工业富联，启动 subagent，输出正式深度报告`",
            "- `local-bank-research 研究江苏银行，重点拆利润桥、资产质量、区域beta、分红和估值预期差`",
            "",
            "估值与建模：",
            "",
            "- `growth-stock-valuation 基于东山精密前置深研和估值接力输入，做目标市值、PEG、一致预期差和赔率判断`",
            "- `financial-modeling 基于东山精密_dcf_financial_model_handoff.md 生成 PEG-ready 和 DCF-ready 数据包`",
            "- `dcf-model 基于东山精密_dcf_ready_package.md 生成 DCF 模型、估值摘要和 validation`",
            "- `integrated-growth-valuation 聚合东山精密 PEG 输出和 DCF 输出，生成统一估值摘要和 scorecard`",
            "",
            "数据：",
            "",
            "- `akshare 获取东山精密近一年行情、估值和财务数据，并做简要趋势分析`",
            "- `tushare 导出东山精密近三年财务指标、估值和日行情，整理成表格`",
            "- `wencai-query 查询最近10日涨停次数最多的A股，导出表格`",
            "",
            "输出、发布和工具：",
            "",
            "- `finance-research-xhs 把东山精密研究报告改写成小红书长文本笔记`",
            "- `markdown-report-pdf 把东山精密研究报告转成正式 PDF`",
            "- `research-report-publication-editor 审校东山精密终稿，清理内部痕迹和工具痕迹`",
            "- `frontend-design 做一个AI算力供应链研究仪表盘，包含公司对比、催化事件和风险提示`",
            "- `doc 把东山精密研究报告整理成docx，保留标题层级、表格和风险提示`",
            "- `find-skills 找一个适合做A股公告跟踪和财报解析的skill`",
            "- `skill-github-sync 重新同步本地skills到GitHub仓库，并更新README`",
            "- `feishu-codex-research-bridge 查看飞书投研队列，确认当前运行任务和结果发送状态`",
            "",
            "2. 不点名技能的自然语言调用：",
            "",
            "研究与跟踪：",
            "",
            "- `调研东山精密，重点看4月9日前后是否有订单、客户、财报或市场行为催化；启动 subagent，输出证据链和后续跟踪清单`",
            "- `研究AI服务器产业链，启动 subagent，拆分上游材料、PCB、连接器、电源、液冷和整机环节，输出完整产业链深度报告`",
            "- `研究东山精密，启动 subagent，重点看市场重定价、旧业务底盘、第二成长曲线、平台复用能力、竞争客户验证、利润桥和估值接力输入`",
            "- `调研工业富联，启动 subagent，重点看AI服务器订单、客户结构、供应链地位、利润释放和估值接力输入`",
            "- `研究江苏银行，重点拆利润桥、资产质量、区域beta、债券投资、分红和估值预期差`",
            "- `持续跟踪东山精密的新订单、客户验证、财报和市场行为，判断逻辑是否强化或证伪`",
            "",
            "估值与建模：",
            "",
            "- `growth-stock-valuation 基于东山精密前置深研和估值接力输入，做目标市值、PEG、一致预期差和赔率判断`",
            "- `基于东山精密正式研究输出，先做三表和现金流建模，再分别跑 PEG 和 DCF，最后聚合成统一估值摘要`",
            "- `用官方 dcf-model 对东山精密 DCF-ready 数据包做现金流折现、敏感性分析和模型校验`",
            "- `把 PEG 和 DCF 两个模型结果合并成一份估值 scorecard，列出关键假设、差异和证伪点`",
            "",
            "数据：",
            "",
            "- `获取东山精密近一年行情、估值和财务数据，并做简要趋势分析`",
            "- `导出东山精密近三年财务指标、估值和日行情，整理成表格`",
            "- `查询最近10日涨停次数最多的A股，导出表格`",
            "",
            "输出、发布和工具：",
            "",
            "- `把东山精密研究报告改写成小红书长文本笔记，保留证据链、风险和假设分层`",
            "- `把东山精密研究报告转成带目录、页眉页脚和中文排版的 PDF`",
            "- `审校这份投研终稿，删除工具痕迹、内部审稿语言和不适合对外发布的措辞`",
            "- `做一个AI算力供应链研究仪表盘，包含公司对比、催化事件、估值和风险提示`",
            "- `把东山精密研究报告整理成docx，保留标题层级、表格和风险提示`",
            "- `帮我找一个适合做A股公告跟踪和财报解析的skill`",
            "- `重新同步我的本地skills仓库，并更新GitHub仓库README`",
            "- `看看飞书投研队列现在有多少任务，正在跑哪个任务`",
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
        ]
    )


def update_readme(repo: Path, skills: list[Path], dry_run: bool) -> None:
    readme = repo / "README.md"
    entries = []
    for skill in sorted(skills, key=lambda item: item.name):
        desc = parse_description(skill / "SKILL.md")
        entries.append(f"- `{skill.name}`: {desc}")

    header = "\n".join(
        [
            "# Wayne's Skill",
            "",
            "Personal Codex skills maintained as versioned assets.",
            "",
            "## Skills",
            "",
            *entries,
            "",
        ]
    )
    tail = default_readme_tail()
    if readme.exists():
        existing = readme.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?m)^## (估值链路|如何调用技能)\s*$", existing)
        if match:
            tail = existing[match.start() :].strip()
    content = f"{header}{tail}\n"
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
