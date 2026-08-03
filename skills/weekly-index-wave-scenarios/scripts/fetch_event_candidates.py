#!/usr/bin/env python3
"""Fetch Tushare major-news candidates for manual policy/IPO event review."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

import pandas as pd
import tushare as ts

DEFAULT_KEYWORDS = [
    "国务院", "证监会", "中国人民银行", "央行", "降准", "降息", "LPR", "MLF", "社融",
    "资本市场", "IPO", "首次公开发行", "上市", "注册", "发行", "招股", "辅导备案",
]


def first_column(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    return next((column for column in candidates if column in frame.columns), None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYYMMDD or Tushare-supported date format")
    parser.add_argument("--end", required=True, help="YYYYMMDD or Tushare-supported date format")
    parser.add_argument("--keywords", default="", help="comma-separated additional terms, e.g. 智谱,长鑫,IPO")
    parser.add_argument("--source", help="optional Tushare major_news source")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise SystemExit("TUSHARE_TOKEN is not configured. Export it before fetching candidates.")

    request = {"start_date": args.start, "end_date": args.end}
    if args.source:
        request["src"] = args.source
    try:
        news = ts.pro_api(token).major_news(**request)
    except Exception as exc:
        raise SystemExit(
            "Tushare major_news is unavailable for this token. "
            "Use a token with major_news access or populate the reviewed ledger from official "
            f"policy/exchange/company sources. Tushare response: {exc}"
        ) from exc
    if news.empty:
        print("No major-news rows returned; check date range, source, and Tushare permissions.")
        return
    title_col = first_column(news, ["title", "name"])
    content_col = first_column(news, ["content", "summary", "description"])
    time_col = first_column(news, ["datetime", "pub_time", "date", "ann_date"])
    source_col = first_column(news, ["src", "source"])
    url_col = first_column(news, ["url", "link"])
    if not title_col or not time_col:
        raise SystemExit(f"Unexpected major_news schema; available columns: {list(news.columns)}")

    terms = DEFAULT_KEYWORDS + [term.strip() for term in args.keywords.split(",") if term.strip()]
    searchable = news[title_col].fillna("")
    if content_col:
        searchable = searchable + " " + news[content_col].fillna("")
    matched = news[searchable.str.contains("|".join(map(__import__("re").escape, terms)), case=False, regex=True, na=False)].copy()
    rows: list[dict] = []
    for row in matched.itertuples(index=False):
        data = row._asdict()
        title = str(data[title_col])
        published_at = str(data[time_col])
        identity = hashlib.sha1(f"{published_at}|{title}".encode("utf-8")).hexdigest()[:12]
        matched_terms = [term for term in terms if term.lower() in (title + " " + str(data.get(content_col, ""))).lower()]
        rows.append({
            "candidate_id": f"tushare-{identity}",
            "published_at": published_at,
            "title": title,
            "source": data.get(source_col, "tushare_major_news"),
            "source_url": data.get(url_col, ""),
            "matched_terms": ",".join(matched_terms),
            "review_status": "pending",
            "review_note": "Verify against an official source before adding to the scored event ledger.",
        })
    candidates = pd.DataFrame(rows).sort_values("published_at", ascending=False) if rows else pd.DataFrame(columns=["candidate_id", "published_at", "title", "source", "source_url", "matched_terms", "review_status", "review_note"])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(output, index=False)
    print(f"Fetched {len(news)} major-news rows; wrote {len(candidates)} review candidates to {output}")


if __name__ == "__main__":
    main()
