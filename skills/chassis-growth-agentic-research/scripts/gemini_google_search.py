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


def _extract_grounding_urls(response: object) -> list[dict[str, str]]:
    """Best-effort extraction of Google Search grounding URLs."""
    seen: set[str] = set()
    urls: list[dict[str, str]] = []
    for candidate in getattr(response, "candidates", []) or []:
        metadata = getattr(candidate, "grounding_metadata", None)
        for chunk in getattr(metadata, "grounding_chunks", []) or []:
            web = getattr(chunk, "web", None)
            uri = getattr(web, "uri", "") if web else ""
            if not uri or uri in seen:
                continue
            seen.add(uri)
            urls.append(
                {
                    "title": getattr(web, "title", "") or "",
                    "url": uri,
                }
            )
    return urls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search/research question")
    parser.add_argument(
        "--model",
        default=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        help="Gemini model name; override with GEMINI_MODEL if needed",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--prompt-prefix",
        default=(
            "你是成长股证券研究证据搜集助手。请用 Google Search 高召回查找资料，"
            "优先公告、交易所、公司官网、投资者关系、客户/竞品公告、券商研报摘要、行业机构。"
            "输出必须区分：公告事实、行业/客户资料、券商口径、产业链口径、媒体线索、待复核假设。"
            "重点寻找市场重定价变量、行业经济性、TAM/SAM/SOM、份额、客户验证、平台复用、承接动作和利润桥线索。"
            "每条线索尽量给出来源标题、发布日期、机构/网站、URL、核心假设和仍需复核的问题；没有 URL 的线索必须标注为待补来源。"
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
    prompt = args.prompt_prefix + args.query

    response = client.models.generate_content(
        model=args.model,
        contents=prompt,
        config=types.GenerateContentConfig(tools=[search_tool]),
    )

    text = getattr(response, "text", "") or ""
    grounding_urls = _extract_grounding_urls(response)
    payload = {
        "query": args.query,
        "model": args.model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "warning": "Gemini output is source-discovery only; verify against original sources before using as evidence.",
        "grounding_urls": grounding_urls,
        "text": text,
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"# Gemini Google Search Leads\n\n- Query: {args.query}\n- Model: {args.model}\n- Generated UTC: {payload['generated_at']}\n"
        )
        print("> Warning: Gemini output is source-discovery only; verify against original sources before using as evidence.\n")
        if grounding_urls:
            print("## Grounding URLs\n")
            for idx, item in enumerate(grounding_urls, 1):
                title = item["title"] or item["url"]
                print(f"{idx}. [{title}]({item['url']})")
            print()
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
