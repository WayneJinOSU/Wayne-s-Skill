#!/usr/bin/env python3
"""Fetch Tushare index daily data and aggregate it into Friday-ending weekly OHLCV."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import tushare as ts


def aggregate_weekly(daily: pd.DataFrame) -> pd.DataFrame:
    daily = daily.copy()
    daily["trade_date"] = pd.to_datetime(daily["trade_date"])
    daily = daily.sort_values("trade_date").set_index("trade_date")
    aggregation = {"open": "first", "high": "max", "low": "min", "close": "last"}
    for field in ("vol", "amount"):
        if field in daily.columns:
            aggregation[field] = "sum"
    # Keep the actual last trading date, rather than a future Friday label on a partial week.
    daily["week_bucket"] = daily.index.to_period("W-FRI")
    weekly = daily.groupby("week_bucket").agg(aggregation).dropna(subset=["open", "high", "low", "close"])
    weekly["week_end"] = daily.groupby("week_bucket").apply(lambda group: group.index.max(), include_groups=False)
    weekly = weekly.reset_index(drop=True)
    return weekly[["week_end", *[column for column in weekly.columns if column != "week_end"]]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-code", required=True, help="e.g. 000300.SH")
    parser.add_argument("--start", required=True, help="YYYYMMDD")
    parser.add_argument("--end", default=datetime.now().strftime("%Y%m%d"), help="YYYYMMDD")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise SystemExit("TUSHARE_TOKEN is not configured. Export it before fetching data.")
    if args.start > args.end:
        raise SystemExit("--start must not be later than --end")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pro = ts.pro_api(token)
    daily = pro.index_daily(ts_code=args.index_code, start_date=args.start, end_date=args.end)
    if daily.empty:
        raise SystemExit("Tushare returned no index data; check code, dates, and permissions.")
    required = {"trade_date", "open", "high", "low", "close"}
    missing = required.difference(daily.columns)
    if missing:
        raise SystemExit(f"Unexpected Tushare schema; missing {sorted(missing)}")

    daily = daily.sort_values("trade_date")
    weekly = aggregate_weekly(daily)
    prefix = args.index_code.replace("/", "_")
    daily_path = output_dir / f"{prefix}_daily.csv"
    weekly_path = output_dir / f"{prefix}_weekly.csv"
    daily.to_csv(daily_path, index=False)
    weekly.to_csv(weekly_path, index=False)
    metadata = {
        "source": "tushare.index_daily",
        "index_code": args.index_code,
        "start": args.start,
        "end": args.end,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "daily_rows": len(daily),
        "weekly_rows": len(weekly),
        "daily_file": str(daily_path),
        "weekly_file": str(weekly_path),
    }
    (output_dir / f"{prefix}_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
