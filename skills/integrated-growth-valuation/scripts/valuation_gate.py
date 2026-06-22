#!/usr/bin/env python3
"""Gate integrated growth valuation aggregation artifacts.

This is intentionally lightweight: it catches missing upstream model outputs,
missing aggregate sections, and language that violates the aggregator boundary.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


REQUIRED_REPORT_TERMS = [
    "PEG",
    "DCF",
    "差异",
    "跟踪",
    "证伪",
]

BANNED_TERMS = [
    "买入",
    "卖出",
    "强烈推荐",
    "仓位",
    "梭哈",
    "确定性收益",
    "稳赚",
]

SUSPICIOUS_PATTERNS = [
    r"DCF\s*校验\s*PEG",
    r"PEG\s*修正\s*DCF",
    r"综合目标价",
    r"取\s*平均",
    r"净利润\s*折现",
    r"EBITDA\s*折现",
]


@dataclass
class Finding:
    severity: str
    file: str
    message: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def check_required_files(artifact_dir: Path, target: str) -> list[Finding]:
    files = [
        f"{target}_valuation_aggregate.md",
        f"{target}_valuation_scorecard.md",
        f"{target}_peg_valuation_deepdive.md",
        f"{target}_peg_valuation_scorecard.md",
    ]
    findings: list[Finding] = []
    for name in files:
        path = artifact_dir / name
        if not path.exists():
            severity = "HIGH" if "valuation_aggregate" in name else "MEDIUM"
            findings.append(Finding(severity, str(path), "Required aggregation artifact or upstream model output is missing."))
    return findings


def detect_dcf_mode(artifact_dir: Path, target: str) -> tuple[str | None, list[Finding]]:
    """Detect which DCF output family is available.

    Formal DCF remains the highest-quality path. Scenario and Reverse DCF are
    accepted when they have an assumption ledger, so the aggregate can disclose
    source type and confidence instead of pretending the model is formal.
    """
    findings: list[Finding] = []

    formal_summary = artifact_dir / f"{target}_dcf_summary.md"
    formal_validation = artifact_dir / f"{target}_dcf_validation.json"
    scenario_summary = artifact_dir / f"{target}_scenario_dcf_summary.md"
    scenario_model = artifact_dir / f"{target}_scenario_dcf_model.xlsx"
    scenario_validation = artifact_dir / f"{target}_scenario_dcf_validation.json"
    reverse_summary = artifact_dir / f"{target}_reverse_dcf_summary.md"
    ledger = artifact_dir / f"{target}_dcf_assumption_ledger.md"

    if formal_summary.exists() and formal_validation.exists():
        return "formal", findings

    if scenario_summary.exists():
        if not ledger.exists():
            findings.append(Finding("HIGH", str(ledger), "Scenario DCF output is missing the required assumption ledger."))
        if scenario_model.exists() and not scenario_validation.exists():
            findings.append(Finding("MEDIUM", str(scenario_validation), "Scenario DCF Excel exists but scenario validation JSON is missing."))
        return "scenario", findings

    if reverse_summary.exists():
        if not ledger.exists():
            findings.append(Finding("HIGH", str(ledger), "Reverse DCF output is missing the required assumption ledger."))
        return "reverse", findings

    findings.append(
        Finding(
            "HIGH",
            str(artifact_dir),
            "No DCF output found. Expected Formal DCF, Scenario DCF, or Reverse DCF outputs.",
        )
    )
    return None, findings


def check_report_content(report: Path) -> list[Finding]:
    if not report.exists():
        return []

    text = read_text(report)
    findings: list[Finding] = []

    for term in REQUIRED_REPORT_TERMS:
        if term not in text:
            findings.append(Finding("HIGH", str(report), f"Missing required term or section signal: {term}"))

    for term in BANNED_TERMS:
        if term in text:
            findings.append(Finding("HIGH", str(report), f"Banned investment-advice language found: {term}"))

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            findings.append(Finding("MEDIUM", str(report), f"Suspicious model-boundary language found: {pattern}"))

    if "UFCF" in text and "净利润折现" in text:
        findings.append(Finding("HIGH", str(report), "DCF appears to mix UFCF with net-profit discounting."))

    for phrase in ["我重新计算", "重新测算", "自算", "硬算"]:
        if phrase in text:
            findings.append(Finding("MEDIUM", str(report), f"Aggregator may be recalculating instead of aggregating: {phrase}"))

    return findings


def check_dcf_mode_disclosure(report: Path, dcf_mode: str | None) -> list[Finding]:
    if not report.exists() or dcf_mode is None:
        return []

    text = read_text(report)
    findings: list[Finding] = []

    if dcf_mode == "scenario":
        required_any = ["Scenario DCF", "情景 DCF", "情景DCF"]
        if not any(term in text for term in required_any):
            findings.append(Finding("HIGH", str(report), "Scenario DCF aggregation must explicitly label the DCF mode."))
        disclosure_groups = [
            ("assumption ledger", ["Assumption Ledger", "假设台账"]),
            ("confidence", ["Confidence", "置信度"]),
            ("proxy", ["Proxy", "代理值", "代理"]),
            ("business inference", ["Business Inference", "业务推理", "业务假设"]),
        ]
        for label, terms in disclosure_groups:
            if not any(term in text for term in terms):
                findings.append(Finding("MEDIUM", str(report), f"Scenario DCF aggregation should disclose assumption-ledger signal: {label}"))

    if dcf_mode == "reverse":
        required_any = ["Reverse DCF", "反推", "隐含"]
        if not any(term in text for term in required_any):
            findings.append(Finding("HIGH", str(report), "Reverse DCF aggregation must explicitly label the DCF mode as reverse/implied."))

    if dcf_mode in {"scenario", "reverse"}:
        banned_phrases = ["正式 DCF 完成", "Formal DCF completed", "审计级", "完整 DCF 已完成"]
        for phrase in banned_phrases:
            if phrase in text:
                findings.append(Finding("HIGH", str(report), f"Downgraded DCF mode is misrepresented as formal: {phrase}"))

    return findings


def check_handoff_content(path: Path, required_terms: list[str]) -> list[Finding]:
    if not path.exists():
        return []
    text = read_text(path)
    findings: list[Finding] = []
    for term in required_terms:
        if term not in text:
            findings.append(Finding("MEDIUM", str(path), f"Handoff may be incomplete; missing: {term}"))
    return findings


def check_dcf_model_outputs(artifact_dir: Path, target: str, dcf_mode: str | None) -> list[Finding]:
    findings: list[Finding] = []
    if dcf_mode == "formal":
        validation_path = artifact_dir / f"{target}_dcf_validation.json"
    elif dcf_mode == "scenario":
        validation_path = artifact_dir / f"{target}_scenario_dcf_validation.json"
    else:
        validation_path = None

    if validation_path and validation_path.exists():
        try:
            validation = json.loads(read_text(validation_path))
        except json.JSONDecodeError:
            findings.append(Finding("HIGH", str(validation_path), "DCF validation JSON is invalid."))
        else:
            if validation.get("status") not in {None, "PASS", "SCENARIO_PASS"}:
                findings.append(Finding("HIGH", str(validation_path), "dcf-model validation did not pass."))
            for error in validation.get("errors", []):
                findings.append(Finding("HIGH", str(validation_path), f"DCF validation error: {error}"))

    return findings


def check_peg_model_outputs(artifact_dir: Path, target: str) -> list[Finding]:
    findings: list[Finding] = []
    for name in [
        f"{target}_peg_valuation_deepdive.md",
        f"{target}_peg_valuation_scorecard.md",
    ]:
        path = artifact_dir / name
        if not path.exists():
            findings.append(Finding("MEDIUM", str(path), "Claimed growth-stock-valuation PEG output is missing."))
            continue
        text = read_text(path)
        for term in ["动态 PEG", "复合 PEG", "当前市值", "触发", "证伪"]:
            if term not in text:
                findings.append(Finding("MEDIUM", str(path), f"PEG output may be incomplete; missing: {term}"))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate integrated growth valuation artifacts.")
    parser.add_argument("--artifact-dir", required=True, help="Directory containing research artifacts.")
    parser.add_argument("--target", required=True, help="Target prefix used in artifact filenames.")
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir).expanduser().resolve()
    target = args.target

    findings: list[Finding] = []
    findings.extend(check_required_files(artifact_dir, target))
    dcf_mode, dcf_mode_findings = detect_dcf_mode(artifact_dir, target)
    findings.extend(dcf_mode_findings)
    findings.extend(check_report_content(artifact_dir / f"{target}_valuation_aggregate.md"))
    findings.extend(check_dcf_mode_disclosure(artifact_dir / f"{target}_valuation_aggregate.md", dcf_mode))
    findings.extend(check_dcf_model_outputs(artifact_dir, target, dcf_mode))
    findings.extend(check_peg_model_outputs(artifact_dir, target))

    if not findings:
        print("PASS integrated-growth-valuation gate")
        return 0

    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    findings.sort(key=lambda item: (severity_order.get(item.severity, 9), item.file, item.message))

    for finding in findings:
        print(f"{finding.severity}\t{finding.file}\t{finding.message}")

    return 1 if any(item.severity == "HIGH" for item in findings) else 2


if __name__ == "__main__":
    raise SystemExit(main())
