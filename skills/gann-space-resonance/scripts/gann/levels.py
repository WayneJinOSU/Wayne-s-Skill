from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd


DIVISION_FRACTIONS = [(k / 8.0, f"{k}/8") for k in range(1, 8)] + [
    (1.0 / 3.0, "1/3"),
    (2.0 / 3.0, "2/3"),
]


def _rank_for_fraction(fraction: float) -> int:
    if abs(fraction - 0.5) < 1e-9:
        return 1
    if any(abs(fraction - value) < 1e-9 for value in (3 / 8, 5 / 8, 1 / 3, 2 / 3)):
        return 2
    return 3


def _atr(frame: pd.DataFrame, end_date: pd.Timestamp, length: int = 60) -> float:
    hist = frame.loc[frame["date"] <= end_date].tail(length + 1).copy()
    if len(hist) < 2:
        return float("nan")
    previous = hist["close"].shift(1)
    true_range = pd.concat(
        [hist["high"] - hist["low"], (hist["high"] - previous).abs(), (hist["low"] - previous).abs()],
        axis=1,
    ).max(axis=1)
    return float(true_range.tail(length).mean())


def generate_levels_for_date(
    frame: pd.DataFrame,
    pivots: pd.DataFrame,
    target_date: pd.Timestamp,
    angle_scale: str = "swing",
    circle_anchor_mode: str = "lowest",
) -> pd.DataFrame:
    """Generate levels known before ``target_date`` only."""
    target_date = pd.Timestamp(target_date)
    history = frame.loc[frame["date"] < target_date]
    eligible = pivots.loc[pivots["confirm_date"] < target_date].sort_values("pivot_date")
    if history.empty or eligible.empty:
        return pd.DataFrame()

    rows: list[dict] = []

    def add(
        level: float,
        source: str,
        family: str,
        level_id: str,
        rank: int,
        anchor_date,
        anchor_price: float,
        direction: str = "",
        parameter_group: str = "main",
    ) -> None:
        if np.isfinite(level) and level > 0:
            rows.append(
                {
                    "date": target_date,
                    "level": float(level),
                    "source": source,
                    "source_family": family,
                    "level_id": level_id,
                    "rank": int(rank),
                    "anchor_date": pd.Timestamp(anchor_date),
                    "anchor_price": float(anchor_price),
                    "direction": direction,
                    "parameter_group": parameter_group,
                }
            )

    # Historical market memory levels.
    for pivot in eligible.itertuples(index=False):
        add(
            pivot.price,
            f"historical_{pivot.type}",
            "memory",
            f"memory:{pivot.type}:{pd.Timestamp(pivot.pivot_date).date()}",
            1,
            pivot.pivot_date,
            pivot.price,
            "support" if pivot.type == "L" else "resistance",
        )

    # Division and extension levels from already confirmed swings.
    if len(eligible) >= 2:
        p0, p1 = eligible.iloc[-2], eligible.iloc[-1]
        move = float(p1["price"] - p0["price"])
        for fraction, label in DIVISION_FRACTIONS:
            level = float(p1["price"] - fraction * move)
            add(
                level,
                f"division_{label}",
                "division",
                f"division:{pd.Timestamp(p0['pivot_date']).date()}:{pd.Timestamp(p1['pivot_date']).date()}:{label}",
                _rank_for_fraction(fraction),
                p1["pivot_date"],
                p1["price"],
                "retracement",
            )

    if len(eligible) >= 3:
        p0, p1, p2 = eligible.iloc[-3], eligible.iloc[-2], eligible.iloc[-1]
        first_move = float(p1["price"] - p0["price"])
        for multiple in (1.0, 1.5):
            level = float(p2["price"] + multiple * first_move)
            add(
                level,
                f"extension_{multiple:g}",
                "division",
                f"extension:{pd.Timestamp(p0['pivot_date']).date()}:{pd.Timestamp(p2['pivot_date']).date()}:{multiple:g}",
                2,
                p2["pivot_date"],
                p2["price"],
                "extension",
            )

    # Angle lines from every confirmed major pivot that has a preceding swing.
    for pos in range(1, len(eligible)):
        previous = eligible.iloc[pos - 1]
        anchor = eligible.iloc[pos]
        elapsed = max((target_date - pd.Timestamp(anchor["pivot_date"])).days, 0)
        swing_days = max((pd.Timestamp(anchor["pivot_date"]) - pd.Timestamp(previous["pivot_date"])).days, 1)
        if angle_scale == "swing":
            scale = abs(float(anchor["price"] - previous["price"])) / swing_days
        elif angle_scale == "volatility":
            scale = _atr(frame, pd.Timestamp(anchor["confirm_date"]), 60) * 0.7
        elif angle_scale == "integer":
            scale = 0.5
        else:
            raise ValueError(f"unknown angle scale: {angle_scale}")
        sign = 1.0 if anchor["type"] == "L" else -1.0
        for label, multiplier in (("1x1", 1.0), ("1x2", 0.5), ("2x1", 2.0)):
            level = float(anchor["price"] + sign * scale * multiplier * elapsed)
            add(
                level,
                f"angle_{label}_{angle_scale}",
                "angle",
                f"angle:{pd.Timestamp(anchor['pivot_date']).date()}:{label}:{angle_scale}",
                1 if label == "1x1" else 2,
                anchor["pivot_date"],
                anchor["price"],
                "rising" if sign > 0 else "falling",
                angle_scale,
            )

    # Square-of-9 equivalent levels.  The anchor is updated only when a lower
    # confirmed L pivot becomes known.
    lows = eligible.loc[eligible["type"] == "L"]
    anchors = lows.nsmallest(1, "price") if circle_anchor_mode == "lowest" else lows
    hist_min, hist_max = float(history["low"].min()), float(history["high"].max())
    for anchor in anchors.itertuples(index=False):
        root = sqrt(float(anchor.price))
        for step in range(-20, 21):
            level = (root + step * 0.5) ** 2
            if hist_min * 0.70 <= level <= hist_max * 1.30:
                add(
                    level,
                    f"circle_{step * 90:+d}",
                    "circle",
                    f"circle:{pd.Timestamp(anchor.pivot_date).date()}:{step * 90:+d}",
                    1,
                    anchor.pivot_date,
                    anchor.price,
                    "",
                    circle_anchor_mode,
                )

    # Round-number memory levels are universal and do not require a fitted range.
    current = float(history.iloc[-1]["close"])
    lower = int(max(100, (current * 0.65) // 100 * 100))
    upper = int((current * 1.35) // 100 * 100 + 100)
    for level in range(lower, upper + 1, 100):
        add(
            level,
            "integer_1000" if level % 1000 == 0 else "integer_100",
            "memory",
            f"integer:{level}",
            1 if level % 1000 == 0 else 2,
            history.iloc[0]["date"],
            level,
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.drop_duplicates(["date", "level_id"]).sort_values(["level", "source_family"]).reset_index(drop=True)
