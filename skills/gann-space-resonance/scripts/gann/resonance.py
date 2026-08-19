from __future__ import annotations

import pandas as pd


CLUSTER_COLUMNS = [
    "date",
    "cluster_id",
    "center",
    "min_level",
    "max_level",
    "member_count",
    "source_count",
    "sources",
    "members",
]


def cluster_levels(levels: pd.DataFrame, merge_distance: float = 0.02) -> pd.DataFrame:
    """Cluster mutually close levels; retain only clusters with >=2 families."""
    if levels.empty:
        return pd.DataFrame(columns=CLUSTER_COLUMNS)
    rows: list[dict] = []
    for date, day in levels.groupby("date", sort=True):
        day = day.sort_values("level").reset_index(drop=True)
        groups: list[list[int]] = []
        current: list[int] = []
        for i, row in day.iterrows():
            if not current:
                current = [i]
                continue
            candidate = current + [i]
            values = day.loc[candidate, "level"].astype(float)
            if (values.max() - values.min()) / values.mean() <= merge_distance:
                current.append(i)
            else:
                groups.append(current)
                current = [i]
        if current:
            groups.append(current)

        cluster_no = 0
        for indices in groups:
            members = day.loc[indices]
            families = sorted(members["source_family"].unique())
            if len(families) < 2:
                continue
            cluster_no += 1
            values = members["level"].astype(float)
            rows.append(
                {
                    "date": pd.Timestamp(date),
                    "cluster_id": f"{pd.Timestamp(date).date()}:C{cluster_no:02d}",
                    "center": float(values.mean()),
                    "min_level": float(values.min()),
                    "max_level": float(values.max()),
                    "member_count": int(len(members)),
                    "source_count": int(len(families)),
                    "sources": "|".join(families),
                    "members": "|".join(members["source"].astype(str)),
                }
            )
    return pd.DataFrame(rows, columns=CLUSTER_COLUMNS)


def level_hit(price: float, values, tolerance: float) -> bool:
    return any(abs(float(price) / float(level) - 1.0) <= tolerance for level in values if float(level) > 0)
