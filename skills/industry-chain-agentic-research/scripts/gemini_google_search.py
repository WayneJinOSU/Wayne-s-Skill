#!/usr/bin/env python3
"""Use Gemini Google Search as a high-recall source discovery helper.

This script deliberately treats model output as leads, not evidence.
Use URLs, report names, dates, and claims from the output to fetch and
verify primary or high-quality secondary sources before writing conclusions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search/research question")
    parser.add_argument(
        "--model",
        default=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
        help="Gemini model name; override with GEMINI_MODEL if needed",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--max-leads",
        type=int,
        default=12,
        help="Maximum number of concise leads to request from Gemini",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=1800,
        help="Hard cap for Gemini response tokens; keeps source-discovery output compact",
    )
    parser.add_argument(
        "--prompt-prefix",
        default=(
            "你是证券研究证据搜集助手。请用 Google Search 高召回查找资料，"
            "优先公告、交易所、公司官网、客户/竞品公告、券商研报摘要、行业机构。"
            "只输出线索表，不要写研究报告、摘要长文或投资结论。"
            "最多输出 {max_leads} 条，每条一行，字段为：Lead-ID、来源标题、发布日期、机构/网站、URL、核心说法、证据类型、需复核的问题、建议打开的原始来源。"
            "输出必须区分：公告事实、行业/客户资料、券商口径、产业链口径、媒体线索、待复核假设。"
            "不要给投资建议、目标价或买卖评级。查询："
        ),
    )
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY environment variable.", file=sys.stderr)
        return 2

    try:
        from google import genai
        from google.genai import types
    except Exception as exc:  # pragma: no cover
        print(
            "Missing google-genai package. Install with: pip install google-genai",
            file=sys.stderr,
        )
        print(repr(exc), file=sys.stderr)
        return 3

    client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())
    prompt = args.prompt_prefix.format(max_leads=args.max_leads) + args.query

    response = client.models.generate_content(
        model=args.model,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[search_tool],
            max_output_tokens=args.max_output_tokens,
        ),
    )

    text = getattr(response, "text", "") or ""
    payload = {
        "query": args.query,
        "model": args.model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "warning": "Gemini output is source-discovery only; verify against original sources before using as evidence.",
        "text": text,
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"# Gemini Google Search Leads\n\n- Query: {args.query}\n- Model: {args.model}\n- Generated UTC: {payload['generated_at']}\n")
        print("> Warning: Gemini output is source-discovery only; verify against original sources before using as evidence.\n")
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
