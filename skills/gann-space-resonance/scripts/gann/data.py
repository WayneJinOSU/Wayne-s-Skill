from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume", "amount"]


def load_ohlcv(db_path: str | Path, start: str, end: str) -> pd.DataFrame:
    """Load unadjusted daily bars from a KhQuant security DuckDB file."""
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        frame = connection.execute(
            """
            SELECT CAST(time AS DATE) AS date, open, high, low, close, volume, amount
            FROM kline_1d
            WHERE CAST(time AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
            ORDER BY time
            """,
            [start, end],
        ).df()
    finally:
        connection.close()
    frame["date"] = pd.to_datetime(frame["date"])
    return frame


def audit_ohlcv(frame: pd.DataFrame) -> dict:
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing_columns:
        raise ValueError(f"Missing OHLCV columns: {missing_columns}")

    duplicate_dates = int(frame["date"].duplicated().sum())
    null_counts = {column: int(frame[column].isna().sum()) for column in REQUIRED_COLUMNS}
    invalid_ohlc = int(
        (
            (frame["high"] < frame[["open", "close", "low"]].max(axis=1))
            | (frame["low"] > frame[["open", "close", "high"]].min(axis=1))
            | (frame[["open", "high", "low", "close"]] <= 0).any(axis=1)
        ).sum()
    )
    non_monotonic = not frame["date"].is_monotonic_increasing
    return {
        "rows": int(len(frame)),
        "start": frame["date"].min().strftime("%Y-%m-%d") if len(frame) else None,
        "end": frame["date"].max().strftime("%Y-%m-%d") if len(frame) else None,
        "duplicate_dates": duplicate_dates,
        "null_counts": null_counts,
        "invalid_ohlc_rows": invalid_ohlc,
        "dates_monotonic": not non_monotonic,
        "passed": not missing_columns
        and duplicate_dates == 0
        and invalid_ohlc == 0
        and all(value == 0 for value in null_counts.values())
        and not non_monotonic,
    }
