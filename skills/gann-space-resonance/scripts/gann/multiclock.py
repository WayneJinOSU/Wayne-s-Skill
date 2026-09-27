from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


MAJOR_TRADING_OFFSETS = (21, 34, 55, 89, 144)
LOCAL_TRADING_OFFSETS = (5, 8, 13, 21, 34)
WAVE_DURATION_RATIOS = (0.618, 1.0, 1.618)


WINDOW_COLUMNS = [
    "source_family", "causal_family", "clock", "anchor_date", "anchor_type", "anchor_price",
    "confirm_date", "offset", "ratio", "center_date", "start_date", "end_date", "tolerance",
    "calendar_status", "window_id",
]


def extend_sessions(
    observed_dates: pd.Series,
    projection_end: str | pd.Timestamp | None = None,
    future_sessions: Iterable[str | pd.Timestamp] | None = None,
) -> pd.DataFrame:
    """Return observed and projected sessions with an explicit calendar-quality flag.

    A caller may provide an exchange calendar through ``future_sessions``.  If it
    does not, future weekdays are estimates and are labelled as such; this keeps
    holiday assumptions visible instead of silently treating weekdays as sessions.
    """
    observed = pd.DatetimeIndex(pd.to_datetime(observed_dates).dropna().unique()).sort_values()
    if observed.empty:
        raise ValueError("observed_dates is empty")
    rows = [{"date": date, "session_status": "observed"} for date in observed]
    end = pd.Timestamp(projection_end) if projection_end is not None else observed[-1]
    if end <= observed[-1]:
        return pd.DataFrame(rows)

    if future_sessions is not None:
        future = pd.DatetimeIndex(pd.to_datetime(list(future_sessions))).sort_values()
        future = future[(future > observed[-1]) & (future <= end)]
        status = "exchange_calendar"
    else:
        future = pd.bdate_range(observed[-1] + pd.offsets.BDay(1), end)
        status = "estimated_weekday"
    rows.extend({"date": date, "session_status": status} for date in future)
    return pd.DataFrame(rows).drop_duplicates("date").sort_values("date").reset_index(drop=True)


def generate_trading_windows(
    pivots: pd.DataFrame,
    sessions: pd.DataFrame,
    *,
    source_family: str,
    offsets: Iterable[int],
    tolerance_bars: int = 1,
) -> pd.DataFrame:
    """Project preset trading-bar clocks from causally confirmed pivots.

    The leading edge of a window is trimmed until after ``confirm_index``.  A
    pivot therefore cannot create a window before market participants could
    have known the pivot existed.
    """
    if tolerance_bars < 0:
        raise ValueError("tolerance_bars must be non-negative")
    required = {"pivot_date", "confirm_date", "type", "price", "pivot_index", "confirm_index"}
    missing = required.difference(pivots.columns)
    if missing:
        raise ValueError(f"pivots missing columns: {sorted(missing)}")
    dates = pd.DatetimeIndex(pd.to_datetime(sessions["date"]))
    rows: list[dict] = []
    for pivot in pivots.itertuples(index=False):
        anchor_index = int(pivot.pivot_index)
        confirm_index = int(pivot.confirm_index)
        for offset in offsets:
            center_index = anchor_index + int(offset)
            if center_index >= len(dates):
                continue
            start_index = max(center_index - tolerance_bars, confirm_index + 1)
            end_index = min(center_index + tolerance_bars, len(dates) - 1)
            if start_index > end_index:
                continue
            rows.append(
                {
                    "source_family": source_family,
                    # Natural/trading and major/local clocks all originate in
                    # the same price-pivot mechanism. They are one causal family.
                    "causal_family": "price_pivot_clock",
                    "clock": "trading_bar",
                    "anchor_date": pd.Timestamp(pivot.pivot_date),
                    "anchor_type": pivot.type,
                    "anchor_price": float(pivot.price),
                    "confirm_date": pd.Timestamp(pivot.confirm_date),
                    "offset": int(offset),
                    "ratio": np.nan,
                    "center_date": dates[center_index],
                    "start_date": dates[start_index],
                    "end_date": dates[end_index],
                    "tolerance": int(tolerance_bars),
                    "calendar_status": sessions.iloc[center_index]["session_status"],
                    "window_id": f"{source_family}:{pd.Timestamp(pivot.pivot_date).date()}:{int(offset)}",
                }
            )
    return pd.DataFrame(rows, columns=WINDOW_COLUMNS)


def generate_wave_duration_windows(
    segments: pd.DataFrame,
    sessions: pd.DataFrame,
    *,
    ratios: Iterable[float] = WAVE_DURATION_RATIOS,
    tolerance_bars: int = 1,
    tolerance_days: int = 2,
) -> pd.DataFrame:
    """Project declared wave durations without inferring wave labels from ratios.

    ``segments`` must contain ``segment``, ``start_date``, ``end_date`` and
    ``projection_anchor_date`` and ``projection_anchor_confirm_date``.
    The caller owns the wave interpretation; this function only makes its
    natural-day and trading-bar consequences auditable.
    """
    required = {
        "segment", "start_date", "end_date", "projection_anchor_date", "projection_anchor_confirm_date"
    }
    missing = required.difference(segments.columns)
    if missing:
        raise ValueError(f"segments missing columns: {sorted(missing)}")
    dates = pd.DatetimeIndex(pd.to_datetime(sessions["date"]))
    date_to_index = {date: index for index, date in enumerate(dates)}
    rows: list[dict] = []
    for segment in segments.itertuples(index=False):
        start = pd.Timestamp(segment.start_date)
        end = pd.Timestamp(segment.end_date)
        anchor = pd.Timestamp(segment.projection_anchor_date)
        anchor_confirm = pd.Timestamp(segment.projection_anchor_confirm_date)
        if any(date not in date_to_index for date in (start, end, anchor, anchor_confirm)):
            raise ValueError(f"segment {segment.segment!r} contains a date absent from the session calendar")
        if not start < end <= anchor:
            raise ValueError(f"segment {segment.segment!r} must satisfy start < end <= projection anchor")
        if anchor_confirm < anchor:
            raise ValueError(f"segment {segment.segment!r} anchor confirmation cannot precede its anchor")
        trading_duration = date_to_index[end] - date_to_index[start]
        natural_duration = (end - start).days
        anchor_index = date_to_index[anchor]
        anchor_confirm_index = date_to_index[anchor_confirm]
        scenario = getattr(segment, "scenario", "")
        for ratio in ratios:
            trading_offset = max(1, round(trading_duration * float(ratio)))
            center_index = anchor_index + trading_offset
            if center_index < len(dates):
                start_index = max(anchor_confirm_index + 1, center_index - tolerance_bars)
                end_index = min(len(dates) - 1, center_index + tolerance_bars)
                if start_index <= end_index:
                    rows.append(
                        {
                            "source_family": "wave_duration",
                            "causal_family": "wave_duration",
                            "clock": "wave_trading_bar",
                            "anchor_date": anchor,
                            "anchor_type": str(segment.segment),
                            "anchor_price": np.nan,
                            "confirm_date": anchor_confirm,
                            "offset": trading_offset,
                            "ratio": float(ratio),
                            "center_date": dates[center_index],
                            "start_date": dates[start_index],
                            "end_date": dates[end_index],
                            "tolerance": int(tolerance_bars),
                            "calendar_status": sessions.iloc[center_index]["session_status"],
                            "window_id": f"wave_trading:{scenario}:{segment.segment}:{anchor.date()}:{ratio:g}",
                        }
                    )
            natural_offset = max(1, round(natural_duration * float(ratio)))
            center = anchor + pd.Timedelta(days=natural_offset)
            if center > dates[-1]:
                continue
            natural_start = max(
                center - pd.Timedelta(days=tolerance_days),
                anchor_confirm + pd.Timedelta(days=1),
            )
            natural_end = center + pd.Timedelta(days=tolerance_days)
            if natural_start > natural_end:
                continue
            rows.append(
                {
                    "source_family": "wave_duration",
                    "causal_family": "wave_duration",
                    "clock": "wave_natural_day",
                    "anchor_date": anchor,
                    "anchor_type": str(segment.segment),
                    "anchor_price": np.nan,
                    "confirm_date": anchor_confirm,
                    "offset": natural_offset,
                    "ratio": float(ratio),
                    "center_date": center,
                    "start_date": natural_start,
                    "end_date": natural_end,
                    "tolerance": int(tolerance_days),
                    "calendar_status": "calendar_day",
                    "window_id": f"wave_natural:{scenario}:{segment.segment}:{anchor.date()}:{ratio:g}",
                }
            )
    return pd.DataFrame(rows, columns=WINDOW_COLUMNS)


def multiclock_density(sessions: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    """Count windows, anchors and independent source families per session."""
    sessions = sessions.copy()
    sessions["date"] = pd.to_datetime(sessions["date"])
    windows = windows.copy()
    for column in ("anchor_date", "start_date", "end_date"):
        windows[column] = pd.to_datetime(windows[column])
    rows = []
    for date in pd.to_datetime(sessions["date"]):
        active = windows.loc[(windows["start_date"] <= date) & (windows["end_date"] >= date)]
        rows.append(
            {
                "date": date,
                "window_count": int(active["window_id"].nunique()) if len(active) else 0,
                "anchor_count": int(active["anchor_date"].nunique()) if len(active) else 0,
                "source_family_count": int(active["source_family"].nunique()) if len(active) else 0,
                "independent_family_count": int(active["causal_family"].nunique()) if len(active) else 0,
                "source_families": "|".join(sorted(active["source_family"].dropna().unique())),
                "causal_families": "|".join(sorted(active["causal_family"].dropna().unique())),
                "session_status": sessions.loc[sessions["date"] == date, "session_status"].iloc[0],
            }
        )
    return pd.DataFrame(rows)


def _peer_confirmation(peers: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "symbol", "close"}
    missing = required.difference(peers.columns)
    if missing:
        raise ValueError(f"peer indices require long-form columns: {sorted(required)}")
    data = peers[list(required)].copy()
    data["date"] = pd.to_datetime(data["date"].astype(str))
    data["close"] = pd.to_numeric(data["close"], errors="raise")
    data = data.sort_values(["symbol", "date"])
    grouped = data.groupby("symbol", group_keys=False)
    data["peer_return"] = grouped["close"].pct_change()
    data["peer_ma5"] = grouped["close"].transform(lambda values: values.rolling(5).mean())
    data["peer_ma20"] = grouped["close"].transform(lambda values: values.rolling(20).mean())
    data["peer_up"] = (data["peer_return"] > 0) & (data["close"] > data["peer_ma5"]) & (data["close"] > data["peer_ma20"])
    data["peer_down"] = (data["peer_return"] < 0) & (data["close"] < data["peer_ma5"]) & (data["close"] < data["peer_ma20"])
    daily = data.groupby("date").agg(
        peer_index_count=("symbol", "nunique"),
        peer_up_count=("peer_up", "sum"),
        peer_down_count=("peer_down", "sum"),
    ).reset_index()
    daily["peer_up_ratio"] = daily["peer_up_count"] / daily["peer_index_count"]
    daily["peer_down_ratio"] = daily["peer_down_count"] / daily["peer_index_count"]
    daily["cross_index_confirmation_up"] = (daily["peer_index_count"] >= 2) & (daily["peer_up_ratio"] >= 2 / 3)
    daily["cross_index_confirmation_down"] = (daily["peer_index_count"] >= 2) & (daily["peer_down_ratio"] >= 2 / 3)
    return daily


def build_confirmation_ledger(
    frame: pd.DataFrame,
    breadth: pd.DataFrame | None = None,
    peers: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Describe pivot, breadth and index confirmation separately; do not emit trades."""
    data = frame.copy().sort_values("date").reset_index(drop=True)
    data["return"] = data["close"].pct_change()
    for length in (5, 10, 20):
        data[f"ma{length}"] = data["close"].rolling(length).mean()
    data["amount_ratio20"] = data["amount"] / data["amount"].rolling(20).mean().shift(1)
    spread = (data["high"] - data["low"]).replace(0, np.nan)
    data["close_location"] = (data["close"] - data["low"]) / spread
    prior_4_low = data["low"].shift(1).rolling(4).min()
    prior_4_high = data["high"].shift(1).rolling(4).max()
    data["trailing_low_candidate"] = data["low"] <= prior_4_low
    data["trailing_high_candidate"] = data["high"] >= prior_4_high
    data["bullish_price_reversal"] = (
        (data["return"] > 0) & (data["low"] <= data["low"].shift(1)) & (data["close_location"] >= 0.65)
    )
    data["bearish_price_reversal"] = (
        (data["return"] < 0) & (data["high"] >= data["high"].shift(1)) & (data["close_location"] <= 0.35)
    )
    if breadth is not None and not breadth.empty:
        b = breadth.copy()
        date_col = "date" if "date" in b.columns else "trade_date"
        b["date"] = pd.to_datetime(b[date_col].astype(str))
        if "advance_ratio" not in b:
            if {"up", "traded"}.issubset(b.columns):
                b["advance_ratio"] = pd.to_numeric(b["up"]) / pd.to_numeric(b["traded"])
            else:
                raise ValueError("breadth requires advance_ratio or up/traded")
        keep = [column for column in ("date", "advance_ratio", "equal_weight_ret", "up", "down", "traded") if column in b]
        data = data.merge(b[keep], on="date", how="left")
        data["breadth_reversal_up"] = (data["advance_ratio"] >= 0.65) & (data["advance_ratio"].shift(1) <= 0.35)
        data["breadth_reversal_down"] = (data["advance_ratio"] <= 0.35) & (data["advance_ratio"].shift(1) >= 0.65)
        data["diffusion_confirmation_up"] = (
            (data["return"] > 0)
            & (data["advance_ratio"] >= 0.60)
            & (data["advance_ratio"].shift(1) >= 0.50)
        )
    else:
        data["advance_ratio"] = np.nan
        data["breadth_reversal_up"] = False
        data["breadth_reversal_down"] = False
        data["diffusion_confirmation_up"] = False
    if peers is not None and not peers.empty:
        data = data.merge(_peer_confirmation(peers), on="date", how="left")
        for column in ("cross_index_confirmation_up", "cross_index_confirmation_down"):
            data[column] = data[column].eq(True)
    else:
        data["peer_index_count"] = np.nan
        data["peer_up_count"] = np.nan
        data["peer_down_count"] = np.nan
        data["peer_up_ratio"] = np.nan
        data["peer_down_ratio"] = np.nan
        data["cross_index_confirmation_up"] = False
        data["cross_index_confirmation_down"] = False
    data["index_confirmation_up"] = (
        (data["return"] > 0) & (data["close"] > data["ma5"]) & (data["close"] > data["ma20"])
    )
    data["index_confirmation_down"] = (
        (data["return"] < 0) & (data["close"] < data["ma5"]) & (data["close"] < data["ma20"])
    )
    columns = [
        "date", "open", "high", "low", "close", "return", "amount", "amount_ratio20", "close_location",
        "ma5", "ma10", "ma20", "advance_ratio", "trailing_low_candidate", "trailing_high_candidate",
        "bullish_price_reversal", "bearish_price_reversal", "breadth_reversal_up", "breadth_reversal_down",
        "index_confirmation_up", "index_confirmation_down", "diffusion_confirmation_up",
        "peer_index_count", "peer_up_count", "peer_down_count", "peer_up_ratio", "peer_down_ratio",
        "cross_index_confirmation_up", "cross_index_confirmation_down",
    ]
    return data[columns]
