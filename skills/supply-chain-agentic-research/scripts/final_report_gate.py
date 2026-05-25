#!/usr/bin/env python3
"""Validate that a final_report is a full research report, not a summary."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_REQUIRED_TERMS = [
    "市场正在交易",
    "利润桥",
    "毛利率",
    "现金流",
    "客户",
    "竞争",
    "产能",
    "订单",
    "验证",
    "证伪",
    "敏感性",
    "跟踪",
]

DEFAULT_CONCEPT_GROUPS = {
    "industry_cycle": ["行业周期", "周期位置", "供需", "市场空间", "行业 beta"],
    "technology_value": ["技术路线", "产品代际", "价值量", "ASP", "单机", "单柜", "单车"],
    "competition_customer": ["竞争", "客户认证", "客户链", "份额", "替代风险"],
    "capacity_orders": ["产能", "扩产", "订单", "排产", "出货", "收入确认"],
    "raw_material_price": ["原材料", "价格传导", "顺价", "成本转嫁", "库存重估"],
    "profit_bridge": ["利润桥", "利润中枢", "归母", "少数股东", "投资收益"],
    "sensitivity": ["敏感性", "情景", "底线", "基准", "上行"],
    "tracking": ["跟踪", "绿色", "黄灯", "红色", "警报"],
    "skeptic": ["反方", "证伪", "降级", "悲观派", "替代解释"],
}

SECTION_REQUIRED_SIGNALS = [
    "收入",
    "毛利",
    "现金流",
    "验证",
    "证伪",
    "降级",
    "利润",
    "客户",
    "订单",
    "产能",
]

PROFILE_PRESETS = {
    "compact": {
        "min_cjk": 8000,
        "min_sections": 10,
        "min_tables": 6,
        "min_section_cjk": 350,
        "deep_section_cjk": 1000,
        "min_deep_sections": 0,
    },
    "standard": {
        "min_cjk": 10000,
        "min_sections": 10,
        "min_tables": 8,
        "min_section_cjk": 450,
        "deep_section_cjk": 1000,
        "min_deep_sections": 2,
    },
    "complex": {
        "min_cjk": 12000,
        "min_sections": 12,
        "min_tables": 10,
        "min_section_cjk": 500,
        "deep_section_cjk": 1000,
        "min_deep_sections": 4,
    },
    "long-form": {
        "min_cjk": 15000,
        "min_sections": 12,
        "min_tables": 8,
        "min_section_cjk": 600,
        "deep_section_cjk": 1000,
        "min_deep_sections": 6,
    },
}


def choose_auto_profile(
    market_variables: int | None,
    product_generations: int | None,
    customer_chains: int | None,
    profit_lines: int | None,
) -> str:
    """Choose report depth from variable complexity.

    Missing counts mean the outline did not provide enough metadata; in that
    case, use standard rather than guessing compact.
    """
    counts = [market_variables, product_generations, customer_chains, profit_lines]
    if all(item is None for item in counts):
        return "standard"

    mv = market_variables or 0
    pg = product_generations or 0
    cc = customer_chains or 0
    pl = profit_lines or 0

    if mv >= 9 or pg >= 6 or cc >= 4 or pl >= 4:
        return "complex"
    if mv >= 6 or pg >= 4 or cc >= 3 or pl >= 3:
        return "complex"
    if mv <= 3 and pg <= 2 and cc <= 1 and pl <= 1:
        return "compact"
    return "standard"


def cjk_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def split_h2_sections(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^##\s+(.+)$", text, flags=re.M))
    sections: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        if title in {"主要来源", "参考资料", "附录", "资料来源"}:
            continue
        sections.append((title, text[start:end].strip()))
    return sections


def table_count(text: str) -> int:
    count = 0
    lines = text.splitlines()
    for idx in range(len(lines) - 1):
        if "|" in lines[idx] and re.search(r"\|\s*:?-{3,}:?\s*\|", lines[idx + 1]):
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--profile",
        choices=["auto", "compact", "standard", "complex", "long-form"],
        default="standard",
        help=(
            "Validation profile. Use auto with variable counts to select a "
            "profile from research complexity."
        ),
    )
    parser.add_argument(
        "--market-variable-count",
        type=int,
        help="High-importance market variables identified in market_variables_map.",
    )
    parser.add_argument(
        "--product-generation-count",
        type=int,
        help="Meaningful product generations/routes that require正文机制展开.",
    )
    parser.add_argument(
        "--customer-chain-count",
        type=int,
        help="Customer/competition chains that materially affect verification.",
    )
    parser.add_argument(
        "--profit-line-count",
        type=int,
        help="Distinct profit lines that require separate bridge or sensitivity logic.",
    )
    parser.add_argument("--min-cjk", type=int)
    parser.add_argument("--min-sections", type=int)
    parser.add_argument("--min-tables", type=int)
    parser.add_argument("--min-section-cjk", type=int)
    parser.add_argument("--deep-section-cjk", type=int)
    parser.add_argument(
        "--min-deep-sections",
        type=int,
        help=(
            "Minimum number of long H2 sections. Defaults come from --profile. "
            "Use 0 for compact reports or 6 for long-form/deep reports."
        ),
    )
    parser.add_argument("--min-section-signal-hits", type=int, default=2)
    parser.add_argument("--max-thin-section-ratio", type=float, default=0.25)
    parser.add_argument("--required-term", action="append", default=[])
    parser.add_argument(
        "--skip-concept-groups",
        action="store_true",
        help="Skip default concept group coverage checks.",
    )
    args = parser.parse_args()

    active_profile = args.profile
    if active_profile == "auto":
        active_profile = choose_auto_profile(
            args.market_variable_count,
            args.product_generation_count,
            args.customer_chain_count,
            args.profit_line_count,
        )
    preset = PROFILE_PRESETS[active_profile]
    for key, value in preset.items():
        if getattr(args, key) is None:
            setattr(args, key, value)

    text = args.report.read_text(encoding="utf-8")
    sections = split_h2_sections(text)
    required_terms = args.required_term or DEFAULT_REQUIRED_TERMS

    failures: list[str] = []
    total_cjk = cjk_count(text)
    tables = table_count(text)

    if total_cjk < args.min_cjk:
        failures.append(f"CJK chars {total_cjk} < required {args.min_cjk}")
    if len(sections) < args.min_sections:
        failures.append(f"H2 sections {len(sections)} < required {args.min_sections}")
    if tables < args.min_tables:
        failures.append(f"tables {tables} < required {args.min_tables}")

    thin_sections = [
        title for title, body in sections if cjk_count(body) < args.min_section_cjk
    ]
    deep_sections = [
        title for title, body in sections if cjk_count(body) >= args.deep_section_cjk
    ]
    if sections:
        thin_ratio = len(thin_sections) / len(sections)
        if thin_ratio > args.max_thin_section_ratio:
            failures.append(
                f"thin H2 sections {len(thin_sections)}/{len(sections)} "
                f"> allowed ratio {args.max_thin_section_ratio:.0%}: "
                + "；".join(thin_sections[:8])
            )
    if args.min_deep_sections > 0 and len(deep_sections) < args.min_deep_sections:
        failures.append(
            f"deep H2 sections {len(deep_sections)} < required "
            f"{args.min_deep_sections}; deep threshold={args.deep_section_cjk} CJK chars"
        )

    missing_terms = [term for term in required_terms if term not in text]
    if missing_terms:
        failures.append("missing required terms: " + "、".join(missing_terms))

    if not args.skip_concept_groups:
        missing_groups = []
        for group, terms in DEFAULT_CONCEPT_GROUPS.items():
            if not any(term in text for term in terms):
                missing_groups.append(f"{group}({ '/'.join(terms[:3]) })")
        if missing_groups:
            failures.append("missing concept groups: " + "、".join(missing_groups))

    weak_signal_sections = []
    for title, body in sections:
        hits = sum(1 for signal in SECTION_REQUIRED_SIGNALS if signal in body)
        if hits < args.min_section_signal_hits:
            weak_signal_sections.append(f"{title}({hits})")
    if weak_signal_sections:
        failures.append(
            "sections with too few financial/verification signals: "
            + "；".join(weak_signal_sections[:8])
        )

    print(f"report={args.report}")
    print(f"profile={active_profile}")
    print(f"cjk_chars={total_cjk}")
    print(f"h2_sections={len(sections)}")
    print(f"tables={tables}")
    print(f"thin_sections={len(thin_sections)}")
    print(f"deep_sections={len(deep_sections)}")

    if failures:
        print("FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
