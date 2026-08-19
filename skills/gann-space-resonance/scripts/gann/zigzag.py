from __future__ import annotations

import pandas as pd


PIVOT_COLUMNS = ["pivot_date", "confirm_date", "type", "price", "pivot_index", "confirm_index"]


def confirmed_zigzag(frame: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """Confirm high/low pivots after an opposing high-low move reaches threshold.

    ``confirm_date`` is the earliest date on which the pivot can be known.  The
    final unconfirmed running extreme is deliberately omitted.
    """
    if not 0 < threshold < 1:
        raise ValueError("threshold must be between zero and one")
    if frame.empty:
        return pd.DataFrame(columns=PIVOT_COLUMNS)

    data = frame.reset_index(drop=True)
    peak_i = trough_i = 0
    direction: str | None = None
    pivots: list[dict] = []

    def record(pivot_i: int, confirm_i: int, kind: str, price: float) -> None:
        if pivots and pivots[-1]["type"] == kind:
            raise RuntimeError("zigzag produced consecutive pivots of the same type")
        pivots.append(
            {
                "pivot_date": data.at[pivot_i, "date"],
                "confirm_date": data.at[confirm_i, "date"],
                "type": kind,
                "price": float(price),
                "pivot_index": int(pivot_i),
                "confirm_index": int(confirm_i),
            }
        )

    for i in range(1, len(data)):
        high = float(data.at[i, "high"])
        low = float(data.at[i, "low"])

        if direction is None:
            if high > float(data.at[peak_i, "high"]):
                peak_i = i
            if low < float(data.at[trough_i, "low"]):
                trough_i = i
            rise = high / float(data.at[trough_i, "low"]) - 1.0
            fall = 1.0 - low / float(data.at[peak_i, "high"])
            if rise >= threshold or fall >= threshold:
                if rise >= fall:
                    record(trough_i, i, "L", float(data.at[trough_i, "low"]))
                    direction = "up"
                    peak_i = i
                else:
                    record(peak_i, i, "H", float(data.at[peak_i, "high"]))
                    direction = "down"
                    trough_i = i
            continue

        if direction == "up":
            if high >= float(data.at[peak_i, "high"]):
                peak_i = i
            peak = float(data.at[peak_i, "high"])
            if low <= peak * (1.0 - threshold):
                record(peak_i, i, "H", peak)
                direction = "down"
                trough_i = i
        else:
            if low <= float(data.at[trough_i, "low"]):
                trough_i = i
            trough = float(data.at[trough_i, "low"])
            if high >= trough * (1.0 + threshold):
                record(trough_i, i, "L", trough)
                direction = "up"
                peak_i = i

    return pd.DataFrame(pivots, columns=PIVOT_COLUMNS)
