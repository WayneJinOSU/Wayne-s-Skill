from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gann.baseline import binomial_upper_p_value, random_log_price_hit_mean, union_log_coverage
from gann.data import audit_ohlcv, load_ohlcv
from gann.levels import generate_levels_for_date
from gann.report import verdict_label, write_markdown_reports
from gann.resonance import cluster_levels, level_hit
from gann.windows import add_calendar_windows, generate_time_windows, window_density
from gann.zigzag import confirmed_zigzag


DEFAULT_DB = Path("/Users/a/khquant/data/SH/000001.db")
START = "2021-08-16"
END = "2026-08-14"


def build_level_panel(frame: pd.DataFrame, pivots: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    main_frames = []
    alternative_angles = []
    for date in frame["date"].iloc[1:]:
        main = generate_levels_for_date(frame, pivots, date, angle_scale="swing")
        if not main.empty:
            main_frames.append(main)
        for scale in ("volatility", "integer"):
            alternative = generate_levels_for_date(frame, pivots, date, angle_scale=scale)
            if not alternative.empty:
                alternative_angles.append(alternative.loc[alternative["source_family"] == "angle"])
    main_levels = pd.concat(main_frames, ignore_index=True) if main_frames else pd.DataFrame()
    all_levels = pd.concat([main_levels, *alternative_angles], ignore_index=True)
    return main_levels, all_levels


def _space_candidates(main_levels: pd.DataFrame, all_levels: pd.DataFrame, clusters: pd.DataFrame) -> dict[str, pd.DataFrame]:
    candidates = {
        "division": main_levels.loc[main_levels["source_family"] == "division", ["date", "level"]],
        "memory": main_levels.loc[main_levels["source_family"] == "memory", ["date", "level"]],
        "circle": main_levels.loc[main_levels["source_family"] == "circle", ["date", "level"]],
        "angle_swing": main_levels.loc[
            (main_levels["source_family"] == "angle") & (main_levels["parameter_group"] == "swing"), ["date", "level"]
        ],
        "angle_volatility": all_levels.loc[
            (all_levels["source_family"] == "angle") & (all_levels["parameter_group"] == "volatility"), ["date", "level"]
        ],
        "angle_integer": all_levels.loc[
            (all_levels["source_family"] == "angle") & (all_levels["parameter_group"] == "integer"), ["date", "level"]
        ],
        "all_primary": main_levels[["date", "level"]],
        "clusters_2plus": clusters.rename(columns={"center": "level"})[["date", "level"]],
    }
    return candidates


def evaluate_space(
    pivots: pd.DataFrame,
    candidates: dict[str, pd.DataFrame],
    price_lower: float,
    price_upper: float,
) -> pd.DataFrame:
    rows = []
    for tolerance in (0.025, 0.015):
        for tool, panel in candidates.items():
            by_date = {date: group["level"].astype(float).tolist() for date, group in panel.groupby("date")}
            for direction, kind in (("support", "L"), ("resistance", "H"), ("both", None)):
                targets = pivots if kind is None else pivots.loc[pivots["type"] == kind]
                trial_prices: list[tuple[float, list[float]]] = []
                for pivot in targets.itertuples(index=False):
                    values = by_date.get(pd.Timestamp(pivot.pivot_date), [])
                    if values:
                        trial_prices.append((float(pivot.price), values))
                if not trial_prices:
                    continue
                hits = sum(level_hit(price, values, tolerance) for price, values in trial_prices)
                coverages = [union_log_coverage(values, tolerance, price_lower, price_upper) for _, values in trial_prices]
                baseline = float(np.mean(coverages))
                monte_carlo = random_log_price_hit_mean(
                    [values for _, values in trial_prices], tolerance, price_lower, price_upper, simulations=1000
                )
                trials = len(trial_prices)
                hit_rate = hits / trials
                rows.append(
                    {
                        "dimension": "space",
                        "tool": tool,
                        "direction": direction,
                        "tolerance": tolerance,
                        "successes": int(hits),
                        "trials": int(trials),
                        "hit_rate": hit_rate,
                        "baseline": baseline,
                        "monte_carlo_baseline": monte_carlo,
                        "excess": hit_rate - baseline,
                        "p_value": binomial_upper_p_value(hits, trials, baseline),
                    }
                )
    return pd.DataFrame(rows)


def evaluate_time(pivots: pd.DataFrame, dates: pd.Series, windows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tolerance in (2, 3):
        tol_windows = windows.loc[windows["tolerance_days"] == tolerance]
        for group in ["big", "full", "quarter", "solar_term", "calendar_quarter", "report_deadline"]:
            group_windows = tol_windows.loc[tol_windows["window_set"] == group]
            if group_windows.empty:
                continue
            active_dates = []
            for date in pd.to_datetime(dates):
                active_dates.append(
                    bool(((group_windows["start_date"] <= date) & (group_windows["end_date"] >= date)).any())
                )
            first_active = pd.to_datetime(dates)[np.argmax(active_dates)]
            eligible_dates = pd.to_datetime(dates) >= first_active
            baseline = float(np.mean(np.array(active_dates)[eligible_dates]))
            targets = pivots.loc[pivots["pivot_date"] >= first_active]
            target_hits = [
                bool(
                    (
                        (group_windows["start_date"] <= pd.Timestamp(pivot.pivot_date))
                        & (group_windows["end_date"] >= pd.Timestamp(pivot.pivot_date))
                    ).any()
                )
                for pivot in targets.itertuples(index=False)
            ]
            successes, trials = sum(target_hits), len(target_hits)
            if trials:
                rows.append(
                    {
                        "dimension": "time",
                        "tool": group,
                        "direction": "both",
                        "tolerance": tolerance / 365.0,
                        "successes": successes,
                        "trials": trials,
                        "hit_rate": successes / trials,
                        "baseline": baseline,
                        "monte_carlo_baseline": baseline,
                        "excess": successes / trials - baseline,
                        "p_value": binomial_upper_p_value(successes, trials, baseline),
                    }
                )

        big_windows = tol_windows.loc[tol_windows["window_set"] == "big"]
        if not big_windows.empty:
            density = window_density(dates, big_windows, "big")
            for threshold in (2, 3):
                active = density["density"] >= threshold
                if not active.any():
                    continue
                first_active = density.loc[active, "date"].min()
                eligible = density["date"] >= first_active
                baseline = float(active.loc[eligible].mean())
                active_map = dict(zip(density["date"], active))
                targets = pivots.loc[pivots["pivot_date"] >= first_active]
                hits = [bool(active_map.get(pd.Timestamp(date), False)) for date in targets["pivot_date"]]
                successes, trials = sum(hits), len(hits)
                rows.append(
                    {
                        "dimension": "time",
                        "tool": f"big_density{threshold}",
                        "direction": "both",
                        "tolerance": tolerance / 365.0,
                        "successes": successes,
                        "trials": trials,
                        "hit_rate": successes / trials if trials else float("nan"),
                        "baseline": baseline,
                        "monte_carlo_baseline": baseline,
                        "excess": successes / trials - baseline if trials else float("nan"),
                        "p_value": binomial_upper_p_value(successes, trials, baseline),
                    }
                )
    return pd.DataFrame(rows)


def build_touch_events(
    frame: pd.DataFrame,
    main_levels: pd.DataFrame,
    clusters: pd.DataFrame,
    tolerance: float = 0.01,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    panels = {
        family: group[["date", "level", "source"]].copy()
        for family, group in main_levels.groupby("source_family")
    }
    panels["clusters_2plus"] = clusters.rename(columns={"center": "level", "sources": "source"})[
        ["date", "level", "source"]
    ].copy()
    price = frame.set_index("date")
    events = []
    for tool, panel in panels.items():
        for date, day_levels in panel.groupby("date"):
            if date not in price.index:
                continue
            loc = price.index.get_loc(date)
            if not isinstance(loc, (int, np.integer)) or loc == 0:
                continue
            row = price.iloc[loc]
            previous_close = float(price.iloc[loc - 1]["close"])
            inside = day_levels.loc[
                (row["close"] >= day_levels["level"] * (1 - tolerance))
                & (row["close"] <= day_levels["level"] * (1 + tolerance))
            ].copy()
            if inside.empty:
                continue
            inside["distance"] = (inside["level"] / float(row["close"]) - 1.0).abs()
            candidate = inside.sort_values("distance").iloc[0]
            level = float(candidate["level"])
            lower, upper = level * (1 - tolerance), level * (1 + tolerance)
            if previous_close > upper:
                direction = "support"
            elif previous_close < lower:
                direction = "resistance"
            else:
                continue
            event = {
                "date": date,
                "tool": tool,
                "direction": direction,
                "level": level,
                "close": float(row["close"]),
                "source": candidate["source"],
            }
            for horizon in (5, 10, 20):
                future = price.iloc[loc + 1 : loc + horizon + 1]
                if len(future) < horizon:
                    event[f"success_{horizon}"] = np.nan
                    event[f"favorable_{horizon}"] = np.nan
                    event[f"adverse_{horizon}"] = np.nan
                    continue
                if direction == "support":
                    holds = float(future["close"].min()) >= lower
                    favorable = float(future["high"].max()) / level - 1.0
                    adverse = float(future["low"].min()) / level - 1.0
                    success = holds and favorable >= tolerance
                else:
                    holds = float(future["close"].max()) <= upper
                    favorable = 1.0 - float(future["low"].min()) / level
                    adverse = 1.0 - float(future["high"].max()) / level
                    success = holds and favorable >= tolerance
                event[f"success_{horizon}"] = bool(success)
                event[f"favorable_{horizon}"] = float(favorable)
                event[f"adverse_{horizon}"] = float(adverse)
            events.append(event)
    events_frame = pd.DataFrame(events)
    # Matched control: preserve each event's close-to-level placement, then test
    # every other date whose prior close approaches the pseudo-level from the
    # same side.  This controls for ordinary mean reversion after a >=1% move.
    if not events_frame.empty:
        close_array = price["close"].to_numpy(dtype=float)
        high_array = price["high"].to_numpy(dtype=float)
        low_array = price["low"].to_numpy(dtype=float)
        previous_array = np.roll(close_array, 1)
        future_metrics: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
        for horizon in (5, 10, 20):
            future_min_close = np.full(len(price), np.nan)
            future_max_close = np.full(len(price), np.nan)
            future_max_high = np.full(len(price), np.nan)
            future_min_low = np.full(len(price), np.nan)
            for loc in range(0, len(price) - horizon):
                future_min_close[loc] = close_array[loc + 1 : loc + horizon + 1].min()
                future_max_close[loc] = close_array[loc + 1 : loc + horizon + 1].max()
                future_max_high[loc] = high_array[loc + 1 : loc + horizon + 1].max()
                future_min_low[loc] = low_array[loc + 1 : loc + horizon + 1].min()
            future_metrics[horizon] = (future_min_close, future_max_close, future_max_high, future_min_low)

        for event_index, event in events_frame.iterrows():
            placement = float(event["close"]) / float(event["level"]) - 1.0
            pseudo_level = close_array / (1.0 + placement)
            lower = pseudo_level * (1.0 - tolerance)
            upper = pseudo_level * (1.0 + tolerance)
            for horizon in (5, 10, 20):
                min_close, max_close, max_high, min_low = future_metrics[horizon]
                valid = np.arange(len(price)) < len(price) - horizon
                valid[0] = False
                event_loc = price.index.get_loc(pd.Timestamp(event["date"]))
                if isinstance(event_loc, (int, np.integer)):
                    valid[event_loc] = False
                if event["direction"] == "support":
                    valid &= previous_array > upper
                    success = (min_close >= lower) & (max_high / pseudo_level - 1.0 >= tolerance)
                else:
                    valid &= previous_array < lower
                    success = (max_close <= upper) & (1.0 - min_low / pseudo_level >= tolerance)
                events_frame.at[event_index, f"baseline_{horizon}"] = (
                    float(success[valid].mean()) if valid.any() else np.nan
                )

    summary_rows = []
    if not events_frame.empty:
        for (tool, direction), group in events_frame.groupby(["tool", "direction"]):
            for horizon in (5, 10, 20):
                valid = group.dropna(subset=[f"success_{horizon}"])
                if valid.empty:
                    continue
                summary_rows.append(
                    {
                        "tool": tool,
                        "direction": direction,
                        "horizon": horizon,
                        "events": len(valid),
                        "success_rate": float(valid[f"success_{horizon}"].mean()),
                        "baseline": float(valid[f"baseline_{horizon}"].mean()),
                        "excess": float(
                            valid[f"success_{horizon}"].mean() - valid[f"baseline_{horizon}"].mean()
                        ),
                        "mean_favorable": float(valid[f"favorable_{horizon}"].mean()),
                        "mean_adverse": float(valid[f"adverse_{horizon}"].mean()),
                    }
                )
    summary = pd.DataFrame(summary_rows)
    if not summary.empty:
        summary["p_value"] = summary.apply(
            lambda row: binomial_upper_p_value(
                int(round(row["success_rate"] * row["events"])), int(row["events"]), float(row["baseline"])
            ),
            axis=1,
        )
        summary["p_adjusted"] = np.minimum(1.0, summary["p_value"] * len(summary))
    return events_frame, summary


def current_candidate_levels(
    frame: pd.DataFrame, pivots: pd.DataFrame, latest_clusters: pd.DataFrame, next_date: pd.Timestamp
) -> pd.DataFrame:
    latest_close = float(frame.iloc[-1]["close"])
    rows = []
    if not latest_clusters.empty:
        for cluster in latest_clusters.itertuples(index=False):
            distance = float(cluster.center) / latest_close - 1.0
            if abs(distance) <= 0.20:
                rows.append(
                    {
                        "as_of": frame.iloc[-1]["date"],
                        "target_date": next_date,
                        "kind": "支撑" if distance < 0 else "压力",
                        "level": float(cluster.center),
                        "zone_lower": float(cluster.min_level),
                        "zone_upper": float(cluster.max_level),
                        "distance": distance,
                        "source_count": int(cluster.source_count),
                        "sources": cluster.sources,
                    }
                )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    supports = result.loc[result["kind"] == "支撑"].sort_values("distance", ascending=False).head(6)
    resistances = result.loc[result["kind"] == "压力"].sort_values("distance").head(6)
    return pd.concat([supports, resistances], ignore_index=True)


def plot_study(
    frame: pd.DataFrame,
    pivots: pd.DataFrame,
    density: pd.DataFrame,
    current_levels: pd.DataFrame,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(frame["date"], frame["close"], color="#23395d", linewidth=1.2, label="SSE Composite close")
    for kind, color, marker in (("H", "#1f9d55", "v"), ("L", "#d94841", "^")):
        points = pivots.loc[pivots["type"] == kind]
        ax.scatter(points["pivot_date"], points["price"], color=color, marker=marker, s=38, label=f"ZigZag {kind}")
    dense = density.loc[density["density"] >= 2]
    for date in dense["date"]:
        ax.axvspan(date - pd.Timedelta(hours=12), date + pd.Timedelta(hours=12), color="#d6a84b", alpha=0.08)
    for row in current_levels.itertuples(index=False):
        color = "#d94841" if row.kind == "支撑" else "#1f9d55"
        ax.axhline(row.level, color=color, linewidth=0.7, linestyle="--", alpha=0.55)
    ax.set_title("Shanghai Composite: Gann levels, confirmed 5% ZigZag pivots and dense time windows")
    ax.set_ylabel("Index points")
    ax.grid(alpha=0.18)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the five-year Shanghai Composite Gann event study")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--start", default=START)
    parser.add_argument("--end", default=END)
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    frame = load_ohlcv(args.db, args.start, args.end)
    audit = audit_ohlcv(frame)
    if not audit["passed"]:
        raise RuntimeError(f"data audit failed: {audit}")
    (args.output / "data_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    pivots = confirmed_zigzag(frame, threshold=0.05)
    pivots.to_csv(args.output / "turning_points.csv", index=False)

    main_levels, all_levels = build_level_panel(frame, pivots)
    main_levels.to_csv(args.output / "space_levels.csv", index=False)
    all_levels.loc[all_levels["parameter_group"].isin(["volatility", "integer"])].to_csv(
        args.output / "space_levels_angle_controls.csv", index=False
    )
    clusters = cluster_levels(main_levels, merge_distance=0.02)
    clusters.to_csv(args.output / "clusters.csv", index=False)

    windows_2 = generate_time_windows(pivots, frame["date"].min(), frame["date"].max(), 2)
    windows_3 = generate_time_windows(pivots, frame["date"].min(), frame["date"].max(), 3)
    calendar = add_calendar_windows(frame["date"].min(), frame["date"].max(), 3)
    windows = pd.concat([windows_2, windows_3, calendar], ignore_index=True)
    windows.to_csv(args.output / "time_windows.csv", index=False)
    density = window_density(frame["date"], windows_2, "big")
    density.to_csv(args.output / "time_window_density.csv", index=False)

    candidates = _space_candidates(main_levels, all_levels, clusters)
    space_stats = evaluate_space(
        pivots,
        candidates,
        float(frame["low"].min()),
        float(frame["high"].max()),
    )
    time_stats = evaluate_time(pivots, frame["date"], windows)
    stats = pd.concat([space_stats, time_stats], ignore_index=True)
    family_size = stats.groupby("dimension")["tool"].transform("nunique") * 2
    stats["p_adjusted"] = np.minimum(1.0, stats["p_value"] * family_size)
    stats["verdict"] = stats.apply(verdict_label, axis=1)
    stats.to_csv(args.output / "statistical_results.csv", index=False)

    events, event_summary = build_touch_events(frame, main_levels, clusters, tolerance=0.01)
    events.to_csv(args.output / "support_resistance_events.csv", index=False)
    event_summary.to_csv(args.output / "support_resistance_summary.csv", index=False)

    next_date = frame.iloc[-1]["date"] + pd.offsets.BDay(1)
    next_levels = generate_levels_for_date(frame, pivots, next_date, angle_scale="swing")
    next_clusters = cluster_levels(next_levels, merge_distance=0.02)
    current_levels = current_candidate_levels(frame, pivots, next_clusters, next_date)
    current_levels.to_csv(args.output / "current_levels.csv", index=False)

    assumptions = [
        "用户指定的近5年覆盖文档默认3年/20年区间；终点采用截至2026-08-16可得的最新完整交易日2026-08-14。",
        "指数波段未在交接文档2.2单列，因此使用连续的5% ZigZag确认拐点作为已确认大波段；运行尾端不计入答案集。",
        "角度线的“波段涨跌幅÷日历日”按指数点数/日解释，否则百分比斜率无法直接落到价格轴；波动率法和0.5点/日整数法作为对照。",
        "候选位在目标日前一日生成；只有 confirm_date 严格早于目标日的拐点可作为锚，禁止使用未来确认信息。",
        "拐点命中按影线极值与±2.5%价位带判定，±1.5%为对照；日线数据无法执行分钟级尾盘偷袭极值剔除。",
        "实际触碰事件使用指数±1%入带，从带外首次进入才计一次；未来守住带且产生至少1%有利运动，定义为形成支撑/压力。",
    ]
    write_markdown_reports(args.output, audit, stats, event_summary, current_levels, assumptions)
    plot_study(frame, pivots, density, current_levels, args.output / "gann_overview.png")

    print(json.dumps({
        "audit": audit,
        "pivots": len(pivots),
        "space_levels": len(main_levels),
        "clusters": len(clusters),
        "touch_events": len(events),
        "output": str(args.output.resolve()),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
