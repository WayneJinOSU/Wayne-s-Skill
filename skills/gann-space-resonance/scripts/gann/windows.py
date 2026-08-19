from __future__ import annotations

import pandas as pd


WINDOW_SETS = {
    "big": [45, 49, 56, 60, 90, 120, 144, 180, 270, 360, 450, 540, 630, 720, 810, 900],
    "full": [30, 45, 49, 56, 60, 90, 120, 144, 180, 270, 360, 450, 540, 630, 720, 810, 900],
    "quarter": [90, 180, 270, 360, 450, 540, 630, 720, 810, 900],
}


def generate_time_windows(
    pivots: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    tolerance_days: int = 2,
) -> pd.DataFrame:
    """Create pre-announced natural-day windows from confirmed pivots."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    rows: list[dict] = []
    for pivot in pivots.itertuples(index=False):
        anchor_date = pd.Timestamp(pivot.pivot_date)
        confirm_date = pd.Timestamp(pivot.confirm_date)
        for group, offsets in WINDOW_SETS.items():
            for offset in offsets:
                center = anchor_date + pd.Timedelta(days=offset)
                window_start = center - pd.Timedelta(days=tolerance_days)
                window_end = center + pd.Timedelta(days=tolerance_days)
                # The document requires the anchor to be strictly earlier than
                # target day minus 60 natural days.  Trim the leading part of a
                # tolerance band instead of treating an offset of exactly 60 as
                # valid across the whole band.
                strict_start = anchor_date + pd.Timedelta(days=61)
                window_start = max(window_start, strict_start)
                if window_start > window_end or confirm_date >= window_start:
                    continue
                if window_end < start or window_start > end:
                    continue
                rows.append(
                    {
                        "window_set": group,
                        "anchor_date": anchor_date,
                        "anchor_type": pivot.type,
                        "confirm_date": confirm_date,
                        "offset_days": int(offset),
                        "center_date": center,
                        "start_date": window_start,
                        "end_date": window_end,
                        "tolerance_days": int(tolerance_days),
                        "window_id": f"{group}:{anchor_date.date()}:{offset}",
                    }
                )
    return pd.DataFrame(rows)


def window_density(trading_dates: pd.Series, windows: pd.DataFrame, window_set: str = "big") -> pd.DataFrame:
    subset = windows.loc[windows["window_set"] == window_set]
    rows = []
    for date in pd.to_datetime(trading_dates):
        active = subset.loc[(subset["start_date"] <= date) & (subset["end_date"] >= date)]
        rows.append(
            {
                "date": date,
                "window_set": window_set,
                "density": int(active["window_id"].nunique()),
                "anchor_count": int(active["anchor_date"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def add_calendar_windows(start: pd.Timestamp, end: pd.Timestamp, tolerance_days: int = 3) -> pd.DataFrame:
    """Generate the document's calendar controls as separate groups."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    fixed = {
        "solar_term": [(2, 4), (6, 21), (8, 7), (12, 21)],
        "calendar_quarter": [(3, 31), (6, 30), (9, 30), (12, 31)],
        "report_deadline": [(4, 30), (8, 31), (10, 31)],
    }
    rows = []
    for year in range(start.year, end.year + 1):
        for group, month_days in fixed.items():
            for month, day in month_days:
                center = pd.Timestamp(year=year, month=month, day=day)
                if start - pd.Timedelta(days=tolerance_days) <= center <= end + pd.Timedelta(days=tolerance_days):
                    rows.append(
                        {
                            "window_set": group,
                            "anchor_date": pd.NaT,
                            "anchor_type": "calendar",
                            "confirm_date": pd.NaT,
                            "offset_days": 0,
                            "center_date": center,
                            "start_date": center - pd.Timedelta(days=tolerance_days),
                            "end_date": center + pd.Timedelta(days=tolerance_days),
                            "tolerance_days": tolerance_days,
                            "window_id": f"{group}:{center.date()}",
                        }
                    )
    return pd.DataFrame(rows)
