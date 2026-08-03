#!/usr/bin/env python3
"""Audit supply-chain research artifacts before claiming completion.

The audit is intentionally simple and conservative. It does not create or edit
research files; it only reports the next required workflow step.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


CORE_SEQUENCE = [
    "question",
    "facts_core",
    "evidence_queue",
    "evidence_index",
    "market_variables_map",
    "industry_cycle_supply_demand",
    "architecture_value_ceiling",
    "product_generation_matrix",
    "competition_customer_chain",
    "raw_material_price_chain",
    "capacity_second_curve",
    "orders_business_validation",
    "profit_bridge",
    "tracking_dashboard",
    "midterm_structure_review",
    "skeptic_review",
    "report_outline",
    "brokerage_report",
]

HANDOFF_KEYS = [
    "dcf_financial_model_handoff",
    "peg_valuation_handoff",
]


def infer_prefix(artifact_dir: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    if artifact_dir.name:
        return artifact_dir.name
    raise SystemExit("Could not infer prefix; pass --prefix.")


def artifact_path(artifact_dir: Path, prefix: str, key: str) -> Path:
    return artifact_dir / f"{prefix}_{key}.md"


def run_brokerage_gate(
    args: argparse.Namespace, brokerage_report: Path, market_variables: Path
) -> dict[str, object]:
    script = Path(__file__).with_name("brokerage_report_gate.py")
    cmd = [sys.executable, str(script)]
    if args.profile:
        cmd.extend(["--profile", args.profile])
    if args.market_variable_count is not None:
        cmd.extend(["--market-variable-count", str(args.market_variable_count)])
    if args.product_generation_count is not None:
        cmd.extend(["--product-generation-count", str(args.product_generation_count)])
    if args.customer_chain_count is not None:
        cmd.extend(["--customer-chain-count", str(args.customer_chain_count)])
    if args.profit_line_count is not None:
        cmd.extend(["--profit-line-count", str(args.profit_line_count)])
    if market_variables.exists():
        cmd.extend(["--market-variables-file", str(market_variables)])
    cmd.append(str(brokerage_report))
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "passed": proc.returncode == 0,
    }


def audit(args: argparse.Namespace) -> dict[str, object]:
    artifact_dir = args.artifact_dir.resolve()
    prefix = infer_prefix(artifact_dir, args.prefix)

    if not artifact_dir.exists():
        return {
            "status": "INCOMPLETE",
            "prefix": prefix,
            "artifact_dir": str(artifact_dir),
            "next_action": "create_artifact_dir",
            "missing": [str(artifact_dir)],
        }

    missing = [
        key for key in CORE_SEQUENCE if not artifact_path(artifact_dir, prefix, key).exists()
    ]
    if missing:
        first = missing[0]
        return {
            "status": "INCOMPLETE",
            "prefix": prefix,
            "artifact_dir": str(artifact_dir),
            "next_action": f"write_{first}",
            "missing": missing,
        }

    brokerage_report = artifact_path(artifact_dir, prefix, "brokerage_report")
    brokerage_gate = None
    if not args.skip_brokerage_gate:
        market_variables = artifact_path(artifact_dir, prefix, "market_variables_map")
        brokerage_gate = run_brokerage_gate(args, brokerage_report, market_variables)
        if not brokerage_gate["passed"]:
            return {
                "status": "INCOMPLETE",
                "prefix": prefix,
                "artifact_dir": str(artifact_dir),
                "next_action": "fix_brokerage_report_and_rerun_brokerage_report_gate",
                "missing": [],
                "brokerage_report_gate": brokerage_gate,
            }

    handoff_missing = [
        key for key in HANDOFF_KEYS if not artifact_path(artifact_dir, prefix, key).exists()
    ]
    if handoff_missing:
        return {
            "status": "INCOMPLETE",
            "prefix": prefix,
            "artifact_dir": str(artifact_dir),
            "next_action": "write_post_report_handoffs",
            "missing": handoff_missing,
            "brokerage_report_gate": brokerage_gate,
        }

    stale = []
    report_mtime = brokerage_report.stat().st_mtime
    for key in HANDOFF_KEYS:
        path = artifact_path(artifact_dir, prefix, key)
        if path.stat().st_mtime < report_mtime:
            stale.append(key)
    if stale:
        return {
            "status": "INCOMPLETE",
            "prefix": prefix,
            "artifact_dir": str(artifact_dir),
            "next_action": "regenerate_stale_post_report_handoffs",
            "stale": stale,
            "missing": [],
            "brokerage_report_gate": brokerage_gate,
        }

    return {
        "status": "COMPLETE",
        "prefix": prefix,
        "artifact_dir": str(artifact_dir),
        "next_action": "none",
        "missing": [],
        "brokerage_report_gate": brokerage_gate,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_dir", type=Path)
    parser.add_argument("--prefix")
    parser.add_argument(
        "--profile",
        choices=["auto", "compact", "standard", "complex", "long-form"],
        default="standard",
    )
    parser.add_argument("--market-variable-count", type=int)
    parser.add_argument("--product-generation-count", type=int)
    parser.add_argument("--customer-chain-count", type=int)
    parser.add_argument("--profit-line-count", type=int)
    parser.add_argument("--skip-brokerage-gate", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit(args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']}")
        print(f"prefix={result['prefix']}")
        print(f"artifact_dir={result['artifact_dir']}")
        print(f"next_action={result['next_action']}")
        if result.get("missing"):
            print("missing=" + ",".join(result["missing"]))
        if result.get("stale"):
            print("stale=" + ",".join(result["stale"]))
        brokerage_gate = result.get("brokerage_report_gate")
        if brokerage_gate is not None:
            print("brokerage_report_gate_returncode=" + str(brokerage_gate["returncode"]))
            if brokerage_gate.get("stdout"):
                print(str(brokerage_gate["stdout"]))
            if brokerage_gate.get("stderr"):
                print(str(brokerage_gate["stderr"]), file=sys.stderr)

    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
