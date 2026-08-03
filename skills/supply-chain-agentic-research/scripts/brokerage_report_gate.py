#!/usr/bin/env python3
"""Validate the sell-side style brokerage_report layer.

Internal research artifacts can be evidence-heavy and audit-like; the
brokerage_report must be reader-facing, preserve valuation variables, and
avoid leaking workflow language into the report.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


PROFILE_PRESETS = {
    "compact": {
        "min_cjk": 9500,
        "min_sections": 5,
        "min_tables": 3,
        "max_negative_framing": 32,
        "max_process_language": 4,
    },
    "standard": {
        "min_cjk": 9500,
        "min_sections": 6,
        "min_tables": 4,
        "max_negative_framing": 38,
        "max_process_language": 4,
    },
    "complex": {
        "min_cjk": 9500,
        "min_sections": 7,
        "min_tables": 5,
        "max_negative_framing": 45,
        "max_process_language": 5,
    },
    "long-form": {
        "min_cjk": 12000,
        "min_sections": 8,
        "min_tables": 6,
        "max_negative_framing": 58,
        "max_process_language": 6,
    },
}

SECTION_GROUPS = {
    "investment_summary": ["投资摘要", "核心结论", "核心观点"],
    "company_positioning": ["公司定位", "业务拆分", "业务版图"],
    "industry_trade_spine": ["行业变化", "市场交易主线", "交易主线", "行业周期"],
    "business_growth_logic": ["分业务增长", "增长逻辑", "业务增长", "分业务"],
    "order_quality": ["订单质量", "订单结构", "在手订单", "订单兑现", "订单转收入"],
    "competition_customer_chain": ["竞争格局", "客户认证", "关键竞品", "份额", "供应链位置"],
    "profit_bridge": ["盈利传导", "利润桥", "利润传导"],
    "catalyst_tracking": ["催化剂", "跟踪指标", "跟踪日历", "跟踪体系"],
    "risk_assumption": ["风险提示", "关键假设", "风险"],
}

PREDICTION_VARIABLE_TERMS = [
    ["变量"],
    ["当前判断", "业务定位", "盈利定位", "变量定位"],
    ["是否进入基准假设", "基准假设"],
    ["上行情景", "情景假设", "情景条件"],
    ["对盈利的影响", "盈利传导", "利润传导"],
    ["跟踪指标", "跟踪口径"],
    ["风险处理", "风险触发"],
]

NEGATIVE_FRAMING_RE = re.compile(r"不是|不能|不等于|反证|证伪|降级|闸门")
PROCESS_LANGUAGE_RE = re.compile(
    r"正式报告|正文必须|报告必须|正式报告必须|正确写法|不能写成|"
    r"必须保留|不得|Fact-ID|subagent|skill|闸门补写"
)
FORBIDDEN_BROKERAGE_STYLE_RE = re.compile(
    r"handoff|base\s+driver|scenario\s+driver|tracking-only|quality\s+discount|"
    r"UFCF\s+guardrail|blocking\s+gap|估值接力|接力处理|研报定位|"
    r"本文的核心|变量权重|这张表直接影响\s*DCF",
    flags=re.I,
)
PROHIBITED_VALUATION_RE = re.compile(
    r"目标价|目标市值|买入评级|卖出评级|增持评级|减持评级|强烈推荐|"
    r"合理市值|市值空间|正式估值结论|DCF\s*结论|"
    r"\d+(?:\.\d+)?\s*[xX倍]\s*(?:PE|PEG|P/E)"
)
FACT_ID_RE = re.compile(r"\bF\d{3}\b")

STOP_TOKENS = {
    "变量",
    "市场",
    "口径",
    "证据",
    "等级",
    "成立",
    "不成立",
    "利润",
    "收入",
    "客户",
    "公司",
    "业务",
    "产品",
    "路径",
    "验证",
    "影响",
    "进入",
    "从",
    "到",
    "以及",
}


def choose_auto_profile(
    market_variables: int | None,
    product_generations: int | None,
    customer_chains: int | None,
    profit_lines: int | None,
) -> str:
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


def parse_variable_terms(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    terms: list[str] = []
    lines = text.splitlines()
    in_variable_table = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            in_variable_table = False
            continue
        if stripped.startswith("|") and "变量" in stripped:
            next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
            if re.search(r"\|\s*:?-{3,}:?\s*\|", next_line):
                in_variable_table = True
                continue
        if in_variable_table:
            if not stripped.startswith("|"):
                in_variable_table = False
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells and cells[0] and not set(cells[0]) <= {"-", ":"}:
                terms.append(cells[0])

        match = re.match(r"变量[:：]\s*(.+)", stripped)
        if match:
            terms.append(match.group(1).strip())

    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        cleaned = re.sub(r"[`*_#]", "", term).strip()
        if not cleaned or cleaned in seen or cleaned == "变量":
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return deduped


def tokens_for_term(term: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z]+(?:\d+[A-Za-z]*)?|\d+[A-Za-z]+|[\u4e00-\u9fff]{2,}", term)
    tokens: list[str] = []
    for token in raw_tokens:
        if token in STOP_TOKENS:
            continue
        if len(token) < 2:
            continue
        tokens.append(token)
    return tokens[:8]


def variable_term_hit(report_text: str, term: str) -> bool:
    if term and term in report_text:
        return True
    tokens = tokens_for_term(term)
    if not tokens:
        return False
    hits = sum(1 for token in tokens if token in report_text)
    return hits >= min(2, len(tokens))


def run_publication_hygiene(report: Path) -> dict[str, object]:
    script = (
        Path.home()
        / ".codex"
        / "skills"
        / "research-report-publication-editor"
        / "scripts"
        / "publication_hygiene_gate.py"
    )
    if not script.exists():
        return {
            "ran": False,
            "passed": True,
            "reason": f"publication hygiene script not found: {script}",
        }
    cmd = [sys.executable, str(script), "--fail-on", "medium", "--json", str(report)]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    findings: list[object] = []
    if proc.stdout.strip():
        try:
            findings = json.loads(proc.stdout)
        except json.JSONDecodeError:
            findings = []
    return {
        "ran": True,
        "passed": proc.returncode == 0,
        "returncode": proc.returncode,
        "findings": findings,
        "stderr": proc.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--profile",
        choices=["auto", "compact", "standard", "complex", "long-form"],
        default="standard",
    )
    parser.add_argument("--market-variable-count", type=int)
    parser.add_argument("--product-generation-count", type=int)
    parser.add_argument("--customer-chain-count", type=int)
    parser.add_argument("--profit-line-count", type=int)
    parser.add_argument("--market-variables-file", type=Path)
    parser.add_argument("--required-variable", action="append", default=[])
    parser.add_argument("--min-variable-hits", type=int, default=4)
    parser.add_argument("--min-cjk", type=int)
    parser.add_argument("--min-sections", type=int)
    parser.add_argument("--min-tables", type=int)
    parser.add_argument("--max-negative-framing", type=int)
    parser.add_argument("--max-process-language", type=int)
    parser.add_argument("--max-fact-ids", type=int, default=0)
    parser.add_argument("--skip-hygiene", action="store_true")
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

    text = args.report.read_text(encoding="utf-8", errors="replace")
    sections = split_h2_sections(text)
    tables = table_count(text)
    total_cjk = cjk_count(text)
    negative_framing = len(NEGATIVE_FRAMING_RE.findall(text))
    process_language = len(PROCESS_LANGUAGE_RE.findall(text))
    forbidden_style_hits = sorted(
        {match.group(0) for match in FORBIDDEN_BROKERAGE_STYLE_RE.finditer(text)}
    )
    fact_ids = len(FACT_ID_RE.findall(text))

    failures: list[str] = []
    if total_cjk < args.min_cjk:
        failures.append(f"CJK chars {total_cjk} < required {args.min_cjk}")
    if len(sections) < args.min_sections:
        failures.append(f"H2 sections {len(sections)} < required {args.min_sections}")
    if tables < args.min_tables:
        failures.append(f"tables {tables} < required {args.min_tables}")
    if negative_framing > args.max_negative_framing:
        failures.append(
            f"audit/negative framing terms {negative_framing} > allowed {args.max_negative_framing}"
        )
    if process_language > args.max_process_language:
        failures.append(
            f"workflow/process language terms {process_language} > allowed {args.max_process_language}"
        )
    if forbidden_style_hits:
        failures.append(
            "forbidden system/model-interface language in brokerage report: "
            + "、".join(forbidden_style_hits)
        )
    if fact_ids > args.max_fact_ids:
        failures.append(f"Fact-ID leaks {fact_ids} > allowed {args.max_fact_ids}")
    if PROHIBITED_VALUATION_RE.search(text):
        failures.append("prohibited target-price/rating/formal valuation language detected")

    missing_groups = []
    for group, terms in SECTION_GROUPS.items():
        if not any(term in text for term in terms):
            missing_groups.append(group)
    if missing_groups:
        failures.append("missing brokerage sections/themes: " + "、".join(missing_groups))

    missing_prediction_terms = []
    for choices in PREDICTION_VARIABLE_TERMS:
        if not any(choice in text for choice in choices):
            missing_prediction_terms.append("/".join(choices))
    if missing_prediction_terms:
        failures.append(
            "missing prediction-variable scenario terms: "
            + "、".join(missing_prediction_terms)
        )

    variable_terms = list(args.required_variable)
    if args.market_variables_file:
        variable_terms.extend(parse_variable_terms(args.market_variables_file))
    variable_hits = [
        term for term in variable_terms if variable_term_hit(text, term)
    ]
    required_hits = min(args.min_variable_hits, len(variable_terms))
    if required_hits and len(variable_hits) < required_hits:
        failures.append(
            f"market variable preservation hits {len(variable_hits)} < required {required_hits}"
        )

    hygiene = None
    if not args.skip_hygiene:
        hygiene = run_publication_hygiene(args.report)
        if not hygiene["passed"]:
            findings = hygiene.get("findings") or []
            failures.append(
                "publication hygiene gate failed at medium+: "
                + str(len(findings))
                + " findings"
            )

    print(f"report={args.report}")
    print(f"profile={active_profile}")
    print(f"cjk_chars={total_cjk}")
    print(f"h2_sections={len(sections)}")
    print(f"tables={tables}")
    print(f"negative_framing_terms={negative_framing}")
    print(f"process_language_terms={process_language}")
    print(f"forbidden_style_terms={len(forbidden_style_hits)}")
    print(f"fact_id_leaks={fact_ids}")
    if variable_terms:
        print(f"market_variable_terms={len(variable_terms)}")
        print(f"market_variable_hits={len(variable_hits)}")
    if hygiene is not None:
        print("publication_hygiene=" + ("PASS" if hygiene["passed"] else "FAIL"))

    if failures:
        print("FAIL")
        for item in failures:
            print(f"- {item}")
        if hygiene and not hygiene.get("passed"):
            for finding in (hygiene.get("findings") or [])[:8]:
                if isinstance(finding, dict):
                    print(
                        "- hygiene "
                        + str(finding.get("severity"))
                        + " L"
                        + str(finding.get("line"))
                        + ": "
                        + str(finding.get("text"))
                    )
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
