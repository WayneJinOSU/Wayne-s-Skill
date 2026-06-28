#!/usr/bin/env python3
"""Validate that a chassis-growth final_report is a full report, not a summary."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_REQUIRED_TERMS = [
    "旧业务",
    "第二曲线",
    "利润桥",
    "毛利率",
    "现金流",
    "客户",
    "竞争",
    "验证",
    "证伪",
    "跟踪",
]

DEFAULT_REQUIRED_ANY = {
    "market_spine": ["市场正在交易", "市场重新定价", "市场重新关注", "市场交易变量"],
    "offensive_thesis": ["核心交易逻辑", "核心误定价", "市场误定价", "真正稀缺", "关键瓶颈"],
    "profit_anchor": ["最小利润模型", "单位经济", "数量乘数", "利润中枢区间", "利润中枢"],
    "sharpness_spine": ["最大预期差", "核心分歧", "第一驱动", "核心利润变量", "最短因果链"],
    "base_to_slope_spine": ["旧业务给", "旧业务底盘", "经营下限", "利润斜率", "利润穿透率"],
    "source_expression": ["公司披露", "公告披露", "财报披露", "公司公告", "公告", "财报", "披露", "年报", "半年报", "交易所", "券商假设", "产业链线索"],
}

FRONT_REQUIRED_ANY = [
    "核心交易逻辑",
    "核心误定价",
    "市场误定价",
    "最小利润模型",
    "单位经济",
    "利润中枢区间",
]

FRONT_SHARPNESS_REQUIRED_ANY = [
    "最大预期差",
    "核心分歧",
    "第一驱动",
    "核心利润变量",
    "最短因果链",
]

FRONT_HEDGE_TERMS = [
    "待验证",
    "仍需验证",
    "证据不足",
    "后续关注",
    "不能确认",
    "尚未验证",
    "兑现闸门",
    "风险提示",
    "反方观点",
]

FRONT_INVESTOR_JUDGMENT_TERMS = [
    "我们认为",
    "本报告认为",
    "核心分歧在于",
]

FRONT_PROFIT_TRANSMISSION_TERMS = [
    "利润传导",
    "利润桥",
    "利润弹性",
    "利润斜率",
    "利润中枢",
    "毛利率",
    "费用率",
    "现金流",
]

FRONT_VALIDATION_OR_DOWNGRADE_TERMS = [
    "验证",
    "证伪",
    "降级",
    "若",
]

BANNED_FINAL_REPORT_PATTERNS = [
    ("visible_fact_id", r"\bF\d{3,}\b|\bFact[-_ ]?\d{3,}\b|\bFact-ID\b|\bFact ID\b"),
    ("visible_lead_id", r"\bL\d{3,}\b|\bLead[-_ ]?\d{3,}\b|\bLead-ID\b|\bLead ID\b"),
    ("internal_skill", r"\bskill\b|\bsubagent\b|\bgate\b|\bhandoff\b"),
    ("internal_file_mode", r"\bfinal_report\b|\bbrokerage_report\b|\bsell_side_report\b"),
    ("internal_chinese_trace", r"扩写蓝图|闸门|终稿|研究阶段候选|正确写法|普通投资人最容易误判|本报告只做|提示词|审稿词"),
    ("rating_or_target", r"目标价|目标市值|买入评级|卖出评级|增持评级|减持评级|买入建议|卖出建议|明确投资建议"),
    ("formal_valuation", r"\bPE\b|\bPEG\b|\bDCF\b|SOTP|估值|当前贵不贵"),
]

WRITING_PROCESS_PATTERNS = [
    (
        "research_process_voice",
        r"这轮研究|研究重点|研究抓手|研究路径|研究问题|研究含义|研究框架|研究方法",
    ),
    (
        "report_process_voice",
        r"报告表达|报告写法|正文写法|章节写法|这张竞争表对报告|对报告表达|写法很关键",
    ),
    (
        "meta_judgment_voice",
        r"不应再写成|判断.{0,12}不应只问|真正需要跟踪的是|更有效的研究|更稳妥的处理方式|这套逻辑的优势",
    ),
]

DEFAULT_CONCEPT_GROUPS = {
    "base_business": ["旧业务", "底盘", "现金流", "财务质量"],
    "second_curve": ["第二曲线", "新业务", "天花板", "平台身份"],
    "industry_space": ["行业经济性", "TAM", "SAM", "SOM", "份额"],
    "platform_reuse": ["平台复用", "复用链条", "认证", "良率", "交付"],
    "competition_customer": ["竞争", "客户验证", "份额", "替代风险"],
    "execution": ["承接动作", "扩产", "订单", "量产", "产能"],
    "profit_bridge": ["利润桥", "利润中枢", "费用", "折旧", "少数股东"],
    "tracking": ["跟踪", "绿灯", "黄灯", "红灯", "证伪"],
}

SECTION_REQUIRED_SIGNALS = [
    "收入",
    "毛利",
    "费用",
    "现金流",
    "验证",
    "证伪",
    "降级",
    "利润",
    "客户",
    "订单",
    "产能",
    "份额",
]

DIDACTIC_TERMS = [
    "一般而言",
    "通常来说",
    "从理论上",
    "从框架上",
    "所谓",
    "我们需要理解",
    "接下来需要关注",
    "值得注意的是",
    "需要指出的是",
    "这说明",
    "换句话说",
    "从投资角度看",
    "简单来说",
    "本质上",
]

PARAGRAPH_SIGNAL_TERMS = [
    "公告",
    "财报",
    "披露",
    "年报",
    "交易所",
    "券商假设",
    "产业链",
    "收入",
    "利润",
    "毛利",
    "费用",
    "现金流",
    "客户",
    "订单",
    "产能",
    "份额",
    "验证",
    "证伪",
    "降级",
    "单位经济",
    "数量乘数",
    "第一驱动",
    "核心利润变量",
    "最大预期差",
    "ASP",
    "折旧",
    "财务成本",
    "税率",
    "少数股东",
    "敏感性",
]

PROFILE_PRESETS = {
    "compact": {
        "min_cjk": 5000,
        "min_sections": 6,
        "max_sections": 8,
        "min_tables": 3,
        "min_section_cjk": 300,
        "deep_section_cjk": 900,
        "min_deep_sections": 0,
        "max_didactic_paragraphs": 2,
    },
    "standard": {
        "min_cjk": 7000,
        "min_sections": 7,
        "max_sections": 9,
        "min_tables": 4,
        "min_section_cjk": 400,
        "deep_section_cjk": 900,
        "min_deep_sections": 2,
        "max_didactic_paragraphs": 3,
    },
    "complex": {
        "min_cjk": 10000,
        "min_sections": 8,
        "max_sections": 11,
        "min_tables": 5,
        "min_section_cjk": 450,
        "deep_section_cjk": 1000,
        "min_deep_sections": 3,
        "max_didactic_paragraphs": 4,
    },
    "long-form": {
        "min_cjk": 14000,
        "min_sections": 10,
        "max_sections": 13,
        "min_tables": 6,
        "min_section_cjk": 550,
        "deep_section_cjk": 1000,
        "min_deep_sections": 4,
        "max_didactic_paragraphs": 5,
    },
}


def choose_auto_profile(
    market_variables: int | None,
    second_curves: int | None,
    customer_chains: int | None,
    profit_lines: int | None,
) -> str:
    counts = [market_variables, second_curves, customer_chains, profit_lines]
    if all(item is None for item in counts):
        return "standard"

    mv = market_variables or 0
    sc = second_curves or 0
    cc = customer_chains or 0
    pl = profit_lines or 0

    if mv >= 8 or sc >= 3 or cc >= 4 or pl >= 4:
        return "complex"
    if mv >= 5 or sc >= 2 or cc >= 3 or pl >= 3:
        return "complex"
    if mv <= 3 and sc <= 1 and cc <= 1 and pl <= 1:
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


def split_paragraphs(text: str) -> list[str]:
    paragraphs = []
    for raw in re.split(r"\n\s*\n", text):
        paragraph = raw.strip()
        if not paragraph:
            continue
        if paragraph.startswith("#") or paragraph.startswith("|"):
            continue
        if "```" in paragraph:
            continue
        paragraphs.append(paragraph)
    return paragraphs


def banned_pattern_hits(text: str) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for label, pattern in BANNED_FINAL_REPORT_PATTERNS:
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        if not matches:
            continue
        sample = matches[0].group(0).replace("\n", " ")
        hits.append((label, len(matches), sample))
    return hits


def writing_process_hits(text: str) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for label, pattern in WRITING_PROCESS_PATTERNS:
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        if not matches:
            continue
        sample = matches[0].group(0).replace("\n", " ")
        hits.append((label, len(matches), sample))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--profile",
        choices=["auto", "compact", "standard", "complex", "long-form"],
        default="standard",
    )
    parser.add_argument("--market-variable-count", type=int)
    parser.add_argument("--second-curve-count", type=int)
    parser.add_argument("--customer-chain-count", type=int)
    parser.add_argument("--profit-line-count", type=int)
    parser.add_argument("--min-cjk", type=int)
    parser.add_argument("--min-sections", type=int)
    parser.add_argument("--max-sections", type=int)
    parser.add_argument("--min-tables", type=int)
    parser.add_argument("--min-section-cjk", type=int)
    parser.add_argument("--deep-section-cjk", type=int)
    parser.add_argument("--min-deep-sections", type=int)
    parser.add_argument("--max-didactic-paragraphs", type=int)
    parser.add_argument("--min-section-signal-hits", type=int, default=2)
    parser.add_argument("--max-thin-section-ratio", type=float, default=0.25)
    parser.add_argument("--max-writing-process-hits", type=int, default=0)
    parser.add_argument("--front-window", type=int, default=1500)
    parser.add_argument("--required-term", action="append", default=[])
    parser.add_argument("--skip-concept-groups", action="store_true")
    args = parser.parse_args()

    active_profile = args.profile
    if active_profile == "auto":
        active_profile = choose_auto_profile(
            args.market_variable_count,
            args.second_curve_count,
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
    if args.max_sections is not None and len(sections) > args.max_sections:
        failures.append(
            f"H2 sections {len(sections)} > allowed {args.max_sections}; "
            "merge standalone old-business/second-curve/platform-reuse/"
            "execution/evidence-boundary/profit-calibration chapters into the main spine"
        )
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

    banned_hits = banned_pattern_hits(text)
    if banned_hits:
        details = [
            f"{label}={count}(sample: {sample})"
            for label, count, sample in banned_hits
        ]
        failures.append(
            "banned internal trace or valuation language in final_report: "
            + "；".join(details)
        )

    process_hits = writing_process_hits(text)
    process_hit_count = sum(count for _, count, _ in process_hits)
    if process_hit_count > args.max_writing_process_hits:
        details = [
            f"{label}={count}(sample: {sample})"
            for label, count, sample in process_hits
        ]
        failures.append(
            f"writing/research process voice {process_hit_count} "
            f"> allowed {args.max_writing_process_hits}: "
            + "；".join(details)
        )

    missing_any_groups = []
    for group, terms in DEFAULT_REQUIRED_ANY.items():
        if not any(term in text for term in terms):
            missing_any_groups.append(f"{group}({ '/'.join(terms) })")
    if missing_any_groups:
        failures.append("missing required expression groups: " + "、".join(missing_any_groups))

    front_text = text[: min(len(text), args.front_window)]
    front_hits = sum(1 for term in FRONT_REQUIRED_ANY if term in front_text)
    front_sharp_hits = sum(
        1 for term in FRONT_SHARPNESS_REQUIRED_ANY if term in front_text
    )
    front_investor_hits = sum(
        1 for term in FRONT_INVESTOR_JUDGMENT_TERMS if term in front_text
    )
    front_profit_hits = sum(
        1 for term in FRONT_PROFIT_TRANSMISSION_TERMS if term in front_text
    )
    front_validation_hits = sum(
        1 for term in FRONT_VALIDATION_OR_DOWNGRADE_TERMS if term in front_text
    )
    front_hedge_hits = sum(front_text.count(term) for term in FRONT_HEDGE_TERMS)
    if front_hits == 0:
        failures.append(
            "front section missing offensive thesis/profit model terms: "
            + "、".join(FRONT_REQUIRED_ANY)
        )
    if front_sharp_hits == 0:
        failures.append(
            "front section missing sharp core-logic terms: "
            + "、".join(FRONT_SHARPNESS_REQUIRED_ANY)
        )
    if front_investor_hits == 0:
        failures.append(
            "front section missing investor judgment language: "
            + "、".join(FRONT_INVESTOR_JUDGMENT_TERMS)
        )
    if front_profit_hits == 0:
        failures.append(
            "front section missing profit-transmission language: "
            + "、".join(FRONT_PROFIT_TRANSMISSION_TERMS)
        )
    if front_validation_hits < 2:
        failures.append(
            "front section missing validation/downgrade language: "
            + "、".join(FRONT_VALIDATION_OR_DOWNGRADE_TERMS)
        )
    if front_hedge_hits >= 6 and front_hits < 2:
        failures.append(
            f"front section appears hedge-led: hedge_terms={front_hedge_hits}, "
            f"offensive_terms={front_hits}; move skeptic/risk language later"
        )

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

    didactic_paragraphs = []
    for paragraph in split_paragraphs(text):
        if cjk_count(paragraph) < 60:
            continue
        if not any(term in paragraph for term in DIDACTIC_TERMS):
            continue
        signal_hits = sum(1 for term in PARAGRAPH_SIGNAL_TERMS if term in paragraph)
        has_number = bool(re.search(r"\d", paragraph))
        if signal_hits < 2 and not has_number:
            didactic_paragraphs.append(paragraph[:80].replace("\n", " "))
    if len(didactic_paragraphs) > args.max_didactic_paragraphs:
        failures.append(
            f"didactic low-signal paragraphs {len(didactic_paragraphs)} "
            f"> allowed {args.max_didactic_paragraphs}: "
            + "；".join(didactic_paragraphs[:5])
        )

    print(f"report={args.report}")
    print(f"profile={active_profile}")
    print(f"cjk_chars={total_cjk}")
    print(f"h2_sections={len(sections)}")
    print(f"max_h2_sections={args.max_sections}")
    print(f"tables={tables}")
    print(f"thin_sections={len(thin_sections)}")
    print(f"deep_sections={len(deep_sections)}")
    print(f"didactic_low_signal_paragraphs={len(didactic_paragraphs)}")
    print(f"banned_final_report_hits={sum(count for _, count, _ in banned_hits)}")
    print(f"writing_process_hits={process_hit_count}")
    print(f"front_offensive_terms={front_hits}")
    print(f"front_sharpness_terms={front_sharp_hits}")
    print(f"front_investor_judgment_terms={front_investor_hits}")
    print(f"front_profit_transmission_terms={front_profit_hits}")
    print(f"front_validation_or_downgrade_terms={front_validation_hits}")
    print(f"front_hedge_terms={front_hedge_hits}")
    print(f"front_window={args.front_window}")

    if failures:
        print("FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
