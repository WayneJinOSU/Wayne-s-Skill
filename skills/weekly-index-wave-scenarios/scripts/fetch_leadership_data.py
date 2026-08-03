#!/usr/bin/env python3
"""Fetch a reviewed leader basket and summarise causal weekly leadership state."""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import tushare as ts

REQUIRED = {"ts_code", "name", "role", "theme", "weight", "reviewed_at", "selection_reason"}
VALID_ROLES = {"market_anchor", "style_leader", "narrative_leader"}


def weekly_closes(daily: pd.DataFrame) -> pd.DataFrame:
    daily = daily.copy()
    daily["trade_date"] = pd.to_datetime(daily["trade_date"])
    daily = daily.sort_values("trade_date").set_index("trade_date")
    daily["week_bucket"] = daily.index.to_period("W-FRI")
    weekly = daily.groupby("week_bucket").agg(close=("close", "last"))
    weekly["week_end"] = daily.groupby("week_bucket").apply(lambda group: group.index.max(), include_groups=False)
    return weekly.reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watchlist", required=True)
    parser.add_argument("--start", required=True, help="YYYYMMDD")
    parser.add_argument("--end", default=datetime.now().strftime("%Y%m%d"), help="YYYYMMDD")
    parser.add_argument("--output", required=True)
    parser.add_argument("--pause-seconds", type=float, default=0.2)
    args = parser.parse_args()
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise SystemExit("TUSHARE_TOKEN is not configured. Export it before fetching leader data.")
    roster = pd.read_csv(args.watchlist)
    missing = REQUIRED.difference(roster.columns)
    if missing:
        raise SystemExit(f"Watchlist missing required columns: {sorted(missing)}")
    if not set(roster.role.dropna()).issubset(VALID_ROLES):
        raise SystemExit(f"role must be one of: {sorted(VALID_ROLES)}")
    if roster.ts_code.duplicated().any():
        raise SystemExit("ts_code must be unique in the leader watchlist")
    if args.start > args.end:
        raise SystemExit("--start must not be later than --end")

    pro = ts.pro_api(token)
    summaries: list[dict] = []
    failures: list[dict] = []
    for row in roster.itertuples(index=False):
        try:
            daily = pro.daily(ts_code=row.ts_code, start_date=args.start, end_date=args.end)
            if daily.empty:
                raise ValueError("no daily data")
            weekly = weekly_closes(daily)
            if len(weekly) < 35:
                raise ValueError("fewer than 35 weekly observations")
            weekly["ema13"] = weekly.close.ewm(span=13, adjust=False).mean()
            weekly["ema34"] = weekly.close.ewm(span=34, adjust=False).mean()
            latest = weekly.iloc[-1]
            ret_4w = latest.close / weekly.close.iloc[-5] - 1 if len(weekly) >= 5 else float("nan")
            ret_13w = latest.close / weekly.close.iloc[-14] - 1 if len(weekly) >= 14 else float("nan")
            high_13w = float(weekly.close.iloc[-13:].max())
            low_13w = float(weekly.close.iloc[-13:].min())
            above_ema13 = bool(latest.close >= latest.ema13)
            above_ema34 = bool(latest.close >= latest.ema34)
            if above_ema13 and above_ema34:
                state = "strong" if ret_4w >= 0 else "above_trend_short_pullback"
            elif not above_ema13 and not above_ema34:
                state = "weak" if ret_4w < 0 else "below_trend_rebound"
            else:
                state = "mixed"
            summaries.append({
                "ts_code": row.ts_code, "name": row.name, "role": row.role, "theme": row.theme,
                "weight": float(row.weight), "reviewed_at": row.reviewed_at,
                "latest_week_end": latest.week_end.date().isoformat(), "latest_close": round(float(latest.close), 4),
                "ema13": round(float(latest.ema13), 4), "ema34": round(float(latest.ema34), 4),
                "ret_4w": round(float(ret_4w), 6), "ret_13w": round(float(ret_13w), 6),
                "high_13w": round(high_13w, 4), "low_13w": round(low_13w, 4),
                "above_ema13": above_ema13, "above_ema34": above_ema34, "state": state,
            })
        except Exception as exc:
            failures.append({"ts_code": row.ts_code, "name": row.name, "error": str(exc)})
        time.sleep(max(0, args.pause_seconds))

    if not summaries:
        raise SystemExit(f"No leader summaries produced. Failures: {failures}")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summaries).to_csv(output, index=False)
    metadata = {
        "source": "tushare.daily", "start": args.start, "end": args.end,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(), "leaders_written": len(summaries), "failures": failures,
    }
    output.with_suffix(".metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
