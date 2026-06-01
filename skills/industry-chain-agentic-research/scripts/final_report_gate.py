#!/usr/bin/env python3
"""Validate that an industry final report is not an executive summary."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_REQUIRED_TERMS = [
    "普通投资者导读",
    "产业链",
    "需求",
    "供给",
    "价格",
    "利润池",
    "毛利率",
    "现金流",
    "估值",
    "反证",
    "证伪",
    "跟踪",
]

DEFAULT_CONCEPT_GROUPS = {
    "industry_boundary": ["行业边界", "卖什么", "谁买单", "产业链"],
    "demand": ["需求拆分", "下游需求", "capex", "渗透率", "替换周期"],
    "supply_price": ["供给", "产能", "库存", "价格", "供需"],
    "profit_pool": ["利润池", "议价权", "毛利率", "ROIC", "现金流"],
    "competition_company": ["竞争格局", "重点公司", "份额", "客户", "公司矩阵"],
    "financial_mapping": ["财务映射", "收入", "毛利", "费用", "现金流"],
    "valuation_expectation": ["估值", "市场预期", "隐含情景", "估值分位"],
    "transmission": ["传导链", "利润桥", "BOM", "采购", "收入确认"],
    "skeptic": ["反查", "反证", "替代解释", "降级", "证伪"],
}

SECTION_REQUIRED_SIGNALS = [
    "收入",
    "毛利",
    "现金流",
    "估值",
    "验证",
    "证伪",
    "降级",
    "利润",
    "价格",
    "份额",
]

PROFILE_PRESETS = {
    "compact": {
        "min_cjk": 8000,
        "min_sections": 8,
        "min_tables": 6,
        "min_section_cjk": 350,
        "deep_section_cjk": 900,
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
        "deep_section_cjk": 1100,
        "min_deep_sections": 4,
    },
    "long-form": {
        "min_cjk": 18000,
        "min_sections": 14,
        "min_tables": 12,
        "min_section_cjk": 550,
        "deep_section_cjk": 1200,
        "min_deep_sections": 6,
    },
}


def choose_auto_profile(
    subsegment_count: int | None,
    core_variable_count: int | None,
    profit_pool_count: int | None,
    company_mapping_count: int | None,
) -> str:
    counts = [
        subsegment_count,
        core_variable_count,
        profit_pool_count,
        company_mapping_count,
    ]
    if all(item is None for item in counts):
        return "standard"

    subsegments = subsegment_count or 0
    variables = core_variable_count or 0
    profit_pools = profit_pool_count or 0
    companies = company_mapping_count or 0

    if subsegments >= 7 or variables >= 12 or profit_pools >= 5 or companies >= 12:
        return "long-form"
    if subsegments >= 5 or variables >= 8 or profit_pools >= 3 or companies >= 8:
        return "complex"
    if subsegments <= 3 and variables <= 4 and profit_pools <= 2 and companies <= 5:
        return "compact"
    return "standard"


def cjk_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def split_h2_sections(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^##\s+(.+)$", text, flags=re.M))
    sections: list[tuple[str, str]] = []
    ignored = {"主要来源", "参考资料", "附录", "资料来源", "声明"}
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        if title in ignored:
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
    )
    parser.add_argument("--subsegment-count", type=int)
    parser.add_argument("--core-variable-count", type=int)
    parser.add_argument("--profit-pool-count", type=int)
    parser.add_argument("--company-mapping-count", type=int)
    parser.add_argument("--min-cjk", type=int)
    parser.add_argument("--min-sections", type=int)
    parser.add_argument("--min-tables", type=int)
    parser.add_argument("--min-section-cjk", type=int)
    parser.add_argument("--deep-section-cjk", type=int)
    parser.add_argument("--min-deep-sections", type=int)
    parser.add_argument("--min-section-signal-hits", type=int, default=2)
    parser.add_argument("--max-thin-section-ratio", type=float, default=0.25)
    parser.add_argument("--required-term", action="append", default=[])
    parser.add_argument("--skip-concept-groups", action="store_true")
    args = parser.parse_args()

    active_profile = args.profile
    if active_profile == "auto":
        active_profile = choose_auto_profile(
            args.subsegment_count,
            args.core_variable_count,
            args.profit_pool_count,
            args.company_mapping_count,
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
            f"{args.min_deep_sections}; threshold={args.deep_section_cjk} CJK chars"
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
