#!/usr/bin/env python3
"""Scan research reports for publication hygiene issues."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Finding:
    severity: str
    category: str
    line: int
    page: int | None
    text: str
    suggestion: str


ALLOWED_STRONG_CONSTRAINT = re.compile(
    r"不能把.{0,24}(未披露|订单金额|客户份额|分产品毛利率|未来订单|并购协同利润).{0,12}写成事实"
    r"|合同负债不能等同于完整订单"
    r"|单季现金流改善不能直接外推"
    r"|毛利率修复必须由.{0,24}(产品结构|材料费|费用率).{0,24}验证"
)

WRITING_PROCESS_WORDS = re.compile(r"终稿|报告|正文|章节|结论|写法|最终判断|执行纪律|正式报告|软件章节")


RULES: list[tuple[str, str, str, str]] = [
    (
        "HIGH",
        "导出/任务痕迹",
        r"Markdown Report PDF|Generated through Markdown|HTML/CSS -> PDF|For research discussion only|自然语言_选择合适的skill|启动subagent|_final_report\b",
        "删除生产痕迹；不要进入正式报告正文。",
    ),
    (
        "HIGH",
        "skill/工具痕迹",
        r"所选\s*skill|所用\s*skill|subagent\s*中间产物|growth-stock-valuation|industry-chain-agentic-research|supply-chain-agentic-research|chassis-growth-agentic-research|final_report_gate|闸门补写记录|final_report_expansion_plan",
        "删除工具、skill、subagent 和内部文件名；必要时改为正式来源或内部底稿说明。",
    ),
    (
        "MEDIUM",
        "终稿/流程自述",
        r"终稿(必须|应|不应|采用|不把|把|只保留|因此)|正式报告必须|最终执行纪律|本报告只回答|调用.*skill|进入单公司阶段|正确写法是",
        "改成直接的报告判断句，不要描述写作过程。",
    ),
    (
        "MEDIUM",
        "写作指令口吻",
        r"(报告|正文|章节|结论|写法|最终判断|执行纪律).{0,16}(必须|不能|不得|应当|应该|只能|不应)|(?:必须|不能|不得|应当|应该|只能|不应).{0,16}(写成|写清楚|采用|保留|删除|放在|定义为|处理成)",
        "把写作指令转成研究判断，例如改为“本报告判断/证据边界是/当前更适合定义为/该变量属于/若成立...若不成立...”。",
    ),
    (
        "MEDIUM",
        "指令式语言",
        r"结论不能写成|不能写成强投资判断|正式报告必须|软件章节必须|最终执行纪律是|利润桥不能用收入外推.{0,20}必须拆|终稿.{0,20}(必须|不能|不得|应当|应该|只能|不应)|正确写法是|(?:必须|应当|应该).{0,8}(写清楚|回答)|(?:必须|应当|应该).{0,8}(拆|用|保留|处理|区分|说明).{0,12}(报告|正文|章节|结论|写法)",
        "把写作指令改成研究判断；保留边界，但不要像在执行提示词。",
    ),
    (
        "MEDIUM",
        "提示词/审稿语言",
        r"不进正式主线|不能支撑正文强结论|只能写成行业硬约束|不得|不能替代|不能直接跳到|不能用.*替代",
        "保留证据边界，但改成研究判断语言。",
    ),
    (
        "LOW",
        "教学化/口语化",
        r"这张表说明|普通投资者只要抓住|最小跟踪清单可以压缩为|谁在掏钱|钱买什么|钱最后留在哪|AI 新闻多不多",
        "减少讲课式旁白，改成正式段落承接。",
    ),
]


def extract_pdf_text(path: Path) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except Exception:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        parts = []
        for idx, page in enumerate(reader.pages, 1):
            parts.append(f"\n\fPAGE {idx}\n")
            parts.append(page.extract_text() or "")
        return "\n".join(parts)


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    return path.read_text(encoding="utf-8", errors="replace")


def page_for_line(line: str, current_page: int | None) -> int | None:
    if "\f" in line:
        return (current_page or 0) + 1
    return current_page


def scan(text: str, max_per_rule: int | None = None) -> list[Finding]:
    findings: list[Finding] = []
    per_rule_counts = [0 for _ in RULES]
    global_line = 0
    pages = text.split("\f")
    for page_idx, page_text in enumerate(pages, 1):
        for raw in page_text.splitlines():
            global_line += 1
            line = raw.strip()
            if not line:
                continue
            for idx, (severity, category, pattern, suggestion) in enumerate(RULES):
                if max_per_rule is not None and per_rule_counts[idx] >= max_per_rule:
                    continue
                if category in {"写作指令口吻", "指令式语言"}:
                    if ALLOWED_STRONG_CONSTRAINT.search(line) and not WRITING_PROCESS_WORDS.search(line):
                        continue
                if re.search(pattern, line, flags=re.I):
                    findings.append(
                        Finding(
                            severity=severity,
                            category=category,
                            line=global_line,
                            page=page_idx,
                            text=line[:240],
                            suggestion=suggestion,
                        )
                    )
                    per_rule_counts[idx] += 1
                    break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-per-rule", type=int, default=20)
    parser.add_argument(
        "--fail-on",
        choices=["none", "high", "medium", "low"],
        default="high",
        help="Exit non-zero when findings at or above this severity exist.",
    )
    args = parser.parse_args()

    text = read_text(args.report)
    findings = scan(text, max_per_rule=args.max_per_rule)

    if args.json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    else:
        print(f"report={args.report}")
        print(f"findings={len(findings)}")
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            group = [item for item in findings if item.severity == severity]
            if not group:
                continue
            print(f"\n[{severity}] {len(group)}")
            for item in group:
                loc = f"p{item.page}:" if item.page else ""
                print(f"- {loc}L{item.line} {item.category}: {item.text}")
                print(f"  suggestion: {item.suggestion}")

    order = {"none": 99, "high": 3, "medium": 2, "low": 1}
    severity_value = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    threshold = order[args.fail_on]
    if threshold != 99 and any(severity_value[item.severity] >= threshold for item in findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
