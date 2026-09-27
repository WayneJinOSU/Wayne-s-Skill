#!/usr/bin/env python3
"""Core-stock state breadth vs sector/ETF/index forward risk.

Use Tushare daily data to classify a caller-provided basket of core stocks by
short-window state, then test how state breadth maps to a target instrument's
forward returns and drawdowns.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import tushare as ts


@dataclass(frozen=True)
class Config:
    stocks: dict[str, str]
    target_code: str
    target_name: str
    target_type: str
    analysis_start: str
    fetch_start: str
    end_date: str
    state_window: int
    band: float
    horizons: tuple[int, ...]
    majority_count: int
    output_dir: Path
    force_refresh: bool
    sleep_seconds: float


def parse_stock_items(raw: str) -> dict[str, str]:
    stocks: dict[str, str] = {}
    if not raw:
        return stocks
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            code, name = item.split(":", 1)
        elif "=" in item:
            code, name = item.split("=", 1)
        else:
            code, name = item, item
        stocks[code.strip()] = name.strip() or code.strip()
    return stocks


def load_stocks_file(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    df = pd.read_csv(path)
    code_col = "code" if "code" in df.columns else "ts_code"
    name_col = "name" if "name" in df.columns else None
    if code_col not in df.columns:
        raise ValueError("stocks file must include code or ts_code column")
    return {
        str(row[code_col]).strip(): str(row[name_col]).strip() if name_col else str(row[code_col]).strip()
        for _, row in df.iterrows()
    }


def infer_target_type(code: str) -> str:
    if code.endswith(".CSI") or code.endswith(".SHI") or code.endswith(".SZCI"):
        return "index"
    if code.endswith(".SH") or code.endswith(".SZ"):
        digits = code.split(".")[0]
        if digits.startswith(("15", "51", "56", "58", "59")):
            return "fund"
        return "stock"
    return "index"


def today_yyyymmdd() -> str:
    return datetime.now().strftime("%Y%m%d")


def resolve_end_date(raw: str) -> str:
    value = raw.strip().lower()
    if value in {"", "today", "now", "auto"}:
        return today_yyyymmdd()
    if not re.fullmatch(r"\d{8}", value):
        raise ValueError("--end-date must be YYYYMMDD, today, now, or auto")
    return value


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="核心标的状态扩散对板块/指数/ETF影响复盘")
    parser.add_argument("--stocks", default="", help="逗号分隔: 300308.SZ:中际旭创,300502.SZ:新易盛")
    parser.add_argument("--stocks-file", default=None, help="CSV with code/name columns")
    parser.add_argument("--target-code", required=True, help="观察标的，如 930713.CSI 或 515070.SH")
    parser.add_argument("--target-name", default="", help="观察标的名称")
    parser.add_argument("--target-type", choices=["auto", "index", "fund", "stock"], default="auto")
    parser.add_argument("--analysis-start", default="20250101")
    parser.add_argument("--fetch-start", default="20240101")
    parser.add_argument("--end-date", default="today", help="YYYYMMDD；默认 today，运行时取当天日期")
    parser.add_argument("--state-window", type=int, default=5)
    parser.add_argument("--band", type=float, default=0.05)
    parser.add_argument("--horizons", default="5,10,20")
    parser.add_argument("--majority-count", type=int, default=0, help="默认 floor(n/2)+1")
    parser.add_argument("--output-dir", default="outputs/core_stock_sector_impact")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    args = parser.parse_args()

    stocks = load_stocks_file(args.stocks_file)
    stocks.update(parse_stock_items(args.stocks))
    if not stocks:
        raise ValueError("provide --stocks or --stocks-file")

    horizons = tuple(sorted({int(x.strip()) for x in args.horizons.split(",") if x.strip()}))
    if not horizons:
        raise ValueError("--horizons cannot be empty")
    majority = args.majority_count or (len(stocks) // 2 + 1)
    target_type = infer_target_type(args.target_code) if args.target_type == "auto" else args.target_type
    end_date = resolve_end_date(args.end_date)

    return Config(
        stocks=stocks,
        target_code=args.target_code,
        target_name=args.target_name or args.target_code,
        target_type=target_type,
        analysis_start=args.analysis_start,
        fetch_start=args.fetch_start,
        end_date=end_date,
        state_window=args.state_window,
        band=args.band,
        horizons=horizons,
        majority_count=majority,
        output_dir=Path(args.output_dir),
        force_refresh=args.force_refresh,
        sleep_seconds=args.sleep_seconds,
    )


def ensure_token() -> str:
    token = os.environ.get("TUSHARE_TOKEN") or os.environ.get("TUSHARE_API_TOKEN")
    if not token:
        raise RuntimeError("Missing TUSHARE_TOKEN. Run: export TUSHARE_TOKEN=your_token")
    return token


def cache_path(cache_dir: Path, prefix: str, code: str, start_date: str, end_date: str) -> Path:
    return cache_dir / f"{prefix}_{code.replace('.', '_')}_{start_date}_{end_date}.csv"


def normalize_daily(df: pd.DataFrame, code: str, name: str) -> pd.DataFrame:
    out = df.copy()
    if "trade_date" not in out.columns or "close" not in out.columns:
        raise ValueError(f"{code} data missing trade_date/close")
    out["trade_date"] = pd.to_datetime(out["trade_date"], format="%Y%m%d")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna(subset=["trade_date", "close"]).drop_duplicates("trade_date", keep="last")
    out = out.sort_values("trade_date")
    out["code"] = code
    out["name"] = name
    return out[["trade_date", "code", "name", "close"]]


def load_stock_daily(code: str, name: str, cfg: Config, cache_dir: Path) -> pd.DataFrame:
    path = cache_path(cache_dir, "stock_qfq", code, cfg.fetch_start, cfg.end_date)
    refresh_cache = cfg.force_refresh or cfg.end_date == today_yyyymmdd()
    if path.exists() and not refresh_cache:
        return normalize_daily(pd.read_csv(path), code, name)
    df = ts.pro_bar(ts_code=code, start_date=cfg.fetch_start, end_date=cfg.end_date, adj="qfq", asset="E")
    if df is None or df.empty:
        raise ValueError(f"{code} {name} daily data is empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    time.sleep(cfg.sleep_seconds)
    return normalize_daily(df, code, name)


def load_target_daily(pro, cfg: Config, cache_dir: Path) -> pd.DataFrame:
    path = cache_path(cache_dir, f"target_{cfg.target_type}", cfg.target_code, cfg.fetch_start, cfg.end_date)
    refresh_cache = cfg.force_refresh or cfg.end_date == today_yyyymmdd()
    if path.exists() and not refresh_cache:
        return normalize_daily(pd.read_csv(path), cfg.target_code, cfg.target_name)
    if cfg.target_type == "index":
        df = pro.index_daily(ts_code=cfg.target_code, start_date=cfg.fetch_start, end_date=cfg.end_date)
    elif cfg.target_type == "fund":
        df = pro.fund_daily(ts_code=cfg.target_code, start_date=cfg.fetch_start, end_date=cfg.end_date)
    else:
        df = ts.pro_bar(ts_code=cfg.target_code, start_date=cfg.fetch_start, end_date=cfg.end_date, adj="qfq", asset="E")
    if df is None or df.empty:
        raise ValueError(f"{cfg.target_code} target daily data is empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return normalize_daily(df, cfg.target_code, cfg.target_name)


def build_wide(frames: list[pd.DataFrame]) -> pd.DataFrame:
    wide = None
    for frame in frames:
        col = f"{frame['code'].iloc[0]}|{frame['name'].iloc[0]}"
        one = frame[["trade_date", "close"]].rename(columns={"close": col})
        wide = one if wide is None else wide.merge(one, on="trade_date", how="outer")
    if wide is None:
        raise ValueError("empty stock frames")
    return wide.sort_values("trade_date").set_index("trade_date")


def forward_max_drawdown(close: pd.Series, horizon: int) -> pd.Series:
    """Return the peak-to-trough drawdown observed in each forward window.

    The window includes the observation at ``i`` as the initial peak, followed
    by up to ``horizon`` future observations.  This is a true maximum
    drawdown calculation: a later peak can reset the running high, so a
    subsequent trough is measured from that later peak rather than always from
    the value at ``i``.  A window containing a missing/non-finite value is
    treated as unavailable instead of silently stitching across a data gap.
    """
    values = close.to_numpy(dtype=float)
    result = np.full(len(close), np.nan)
    for i in range(len(close)):
        end = min(i + horizon, len(close) - 1)
        if i + 1 > end:
            continue

        window = values[i : end + 1]
        if not np.isfinite(window).all() or window[0] <= 0:
            continue

        running_peak = np.maximum.accumulate(window)
        drawdowns = window / running_peak - 1
        result[i] = drawdowns[1:].min()
    return pd.Series(result, index=close.index)


def add_forward_metrics(panel: pd.DataFrame, close: pd.Series, prefix: str, horizons: tuple[int, ...]) -> None:
    for horizon in horizons:
        panel[f"{prefix}_fwd_ret_{horizon}d"] = close.shift(-horizon) / close - 1
        panel[f"{prefix}_fwd_dd_{horizon}d"] = forward_max_drawdown(close, horizon)


def classify_detail(ret: pd.DataFrame, band: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    up = ret > band
    down = ret < -band
    sideways = (ret >= -band) & (ret <= band)
    states = pd.DataFrame(index=ret.index)
    for col in ret.columns:
        states[f"{col}|state"] = np.select(
            [up[col], sideways[col], down[col]],
            ["上行", "横盘", "下跌"],
            default=None,
        )
    return up, sideways, down, states


def build_panel(wide: pd.DataFrame, target: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    stock_ret = wide.pct_change(cfg.state_window)
    up, sideways, down, states = classify_detail(stock_ret, cfg.band)
    basket = wide.divide(wide.iloc[0]).mean(axis=1)
    target_close = target.set_index("trade_date")["close"].reindex(wide.index)

    panel = pd.DataFrame(index=wide.index)
    panel["up_count"] = up.sum(axis=1)
    panel["sideways_count"] = sideways.sum(axis=1)
    panel["down_count"] = down.sum(axis=1)
    panel["active_count"] = stock_ret.notna().sum(axis=1)
    panel["core_basket_close"] = basket
    panel["target_close"] = target_close
    for horizon in cfg.horizons:
        panel[f"core_basket_ret_{horizon}d"] = basket.pct_change(horizon)
        panel[f"target_ret_{horizon}d"] = target_close.pct_change(horizon)
    panel[f"core_win_rate_{cfg.state_window}d"] = (stock_ret > 0).mean(axis=1)
    add_forward_metrics(panel, basket, "core_basket", cfg.horizons)
    add_forward_metrics(panel, target_close.dropna(), "target", cfg.horizons)

    panel["regime"] = np.select(
        [
            panel["down_count"] >= cfg.majority_count,
            panel["up_count"] >= cfg.majority_count,
            panel["sideways_count"] >= cfg.majority_count,
        ],
        ["下降扩散", "增长扩散", "横盘钝化"],
        default="混合",
    )
    analysis_start = pd.to_datetime(cfg.analysis_start, format="%Y%m%d")
    panel = panel.loc[panel.index >= analysis_start].copy()
    detail = pd.concat([stock_ret.loc[panel.index], states.loc[panel.index]], axis=1)
    return panel.reset_index(names="trade_date"), detail.reset_index(names="trade_date")


def loss_mean(x: pd.Series) -> float:
    losses = x[x < 0]
    return float(losses.mean()) if len(losses) else 0.0


def summarize(panel: pd.DataFrame, prefix: str, cfg: Config) -> pd.DataFrame:
    required = [f"{prefix}_fwd_ret_{h}d" for h in cfg.horizons]
    valid = panel.dropna(subset=[required[0]]).copy()
    agg: dict[str, tuple[str, str] | tuple[str, object]] = {
        "obs": ("trade_date", "count"),
        "avg_up_count": ("up_count", "mean"),
        "avg_sideways_count": ("sideways_count", "mean"),
        "avg_down_count": ("down_count", "mean"),
    }
    for h in cfg.horizons:
        ret_col = f"{prefix}_fwd_ret_{h}d"
        dd_col = f"{prefix}_fwd_dd_{h}d"
        agg.update(
            {
                f"fwd_{h}d": (ret_col, "mean"),
                f"fwd_{h}d_median": (ret_col, "median"),
                f"fwd_{h}d_p10": (ret_col, lambda x: x.quantile(0.10)),
                f"fwd_{h}d_worst": (ret_col, "min"),
                f"avg_fwd_{h}d_loss": (ret_col, loss_mean),
                f"p10_fwd_dd_{h}d": (dd_col, lambda x: x.quantile(0.10)),
                f"worst_fwd_dd_{h}d": (dd_col, "min"),
            }
        )
    order = ["增长扩散", "横盘钝化", "下降扩散", "混合"]
    return valid.groupby("regime").agg(**agg).reindex(order).reset_index()


def summarize_by_count(panel: pd.DataFrame, count_col: str, prefix: str, cfg: Config) -> pd.DataFrame:
    valid = panel.dropna(subset=[f"{prefix}_fwd_ret_{cfg.horizons[0]}d"]).copy()
    agg: dict[str, tuple[str, str] | tuple[str, object]] = {"obs": ("trade_date", "count")}
    for h in cfg.horizons:
        ret_col = f"{prefix}_fwd_ret_{h}d"
        dd_col = f"{prefix}_fwd_dd_{h}d"
        agg.update(
            {
                f"fwd_{h}d": (ret_col, "mean"),
                f"fwd_{h}d_p10": (ret_col, lambda x: x.quantile(0.10)),
                f"fwd_{h}d_worst": (ret_col, "min"),
                f"avg_fwd_{h}d_loss": (ret_col, loss_mean),
                f"p10_fwd_dd_{h}d": (dd_col, lambda x: x.quantile(0.10)),
                f"worst_fwd_dd_{h}d": (dd_col, "min"),
            }
        )
    return valid.groupby(count_col).agg(**agg).reset_index()



def _valid_outcome(panel: pd.DataFrame, prefix: str, horizon: int) -> pd.DataFrame:
    ret_col = f"{prefix}_fwd_ret_{horizon}d"
    dd_col = f"{prefix}_fwd_dd_{horizon}d"
    cols = ["trade_date", "regime", ret_col, dd_col]
    return panel[cols].replace([np.inf, -np.inf], np.nan).dropna(subset=[ret_col, dd_col]).copy()


def _bootstrap_mean_diff_ci(x: np.ndarray, y: np.ndarray, rng: np.random.Generator,
                             n_boot: int = 2000) -> tuple[float, float]:
    if len(x) == 0 or len(y) == 0:
        return math.nan, math.nan
    if len(x) == 1 and len(y) == 1:
        diff = float(x[0] - y[0])
        return diff, diff
    x_idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    y_idx = rng.integers(0, len(y), size=(n_boot, len(y)))
    diffs = x[x_idx].mean(axis=1) - y[y_idx].mean(axis=1)
    return float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))


def _permutation_pvalue(x: np.ndarray, y: np.ndarray, rng: np.random.Generator,
                        n_perm: int = 2000) -> float:
    if len(x) == 0 or len(y) == 0:
        return math.nan
    observed = float(np.mean(x) - np.mean(y))
    pooled = np.concatenate([x, y])
    n_x = len(x)
    if len(pooled) < 2:
        return math.nan
    extreme = 0
    for _ in range(n_perm):
        shuffled = rng.permutation(pooled)
        diff = float(shuffled[:n_x].mean() - shuffled[n_x:].mean())
        if abs(diff) >= abs(observed) - 1e-15:
            extreme += 1
    return float((extreme + 1) / (n_perm + 1))


def _comparison_stats(x: pd.Series, y: pd.Series, seed: int) -> dict[str, float | bool]:
    x_values = pd.to_numeric(x, errors="coerce").dropna().to_numpy(dtype=float)
    y_values = pd.to_numeric(y, errors="coerce").dropna().to_numpy(dtype=float)
    if len(x_values) == 0 or len(y_values) == 0:
        return {
            "regime_mean": math.nan,
            "baseline_mean": math.nan,
            "increment": math.nan,
            "ci_low": math.nan,
            "ci_high": math.nan,
            "permutation_p": math.nan,
            "significant_05": False,
        }
    rng = np.random.default_rng(seed)
    ci_low, ci_high = _bootstrap_mean_diff_ci(x_values, y_values, rng)
    p_value = _permutation_pvalue(x_values, y_values, rng)
    increment = float(x_values.mean() - y_values.mean())
    return {
        "regime_mean": float(x_values.mean()),
        "baseline_mean": float(y_values.mean()),
        "increment": increment,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "permutation_p": p_value,
        "significant_05": bool(pd.notna(p_value) and p_value < 0.05),
    }


def summarize_baselines(panel: pd.DataFrame, prefix: str, cfg: Config) -> pd.DataFrame:
    """Return explicit unconditional, leave-one-regime-out and trend baselines."""
    rows: list[dict[str, object]] = []
    regime_order = ["增长扩散", "横盘钝化", "下降扩散", "混合"]
    trend_col = f"target_ret_{cfg.state_window}d"
    for horizon in cfg.horizons:
        valid = _valid_outcome(panel, prefix, horizon)
        if valid.empty:
            continue
        ret_col = f"{prefix}_fwd_ret_{horizon}d"
        dd_col = f"{prefix}_fwd_dd_{horizon}d"
        def append_row(baseline_type: str, label: str, sample: pd.DataFrame) -> None:
            if sample.empty:
                return
            rows.append({
                "series": prefix,
                "horizon": horizon,
                "baseline_type": baseline_type,
                "regime": label,
                "obs": int(len(sample)),
                "mean_return": float(sample[ret_col].mean()),
                "positive_rate": float((sample[ret_col] > 0).mean()),
                "mean_max_drawdown": float(sample[dd_col].mean()),
                "p10_return": float(sample[ret_col].quantile(0.10)),
                "p10_max_drawdown": float(sample[dd_col].quantile(0.10)),
                "start_date": sample["trade_date"].min().date().isoformat(),
                "end_date": sample["trade_date"].max().date().isoformat(),
            })
        append_row("unconditional", "全样本", valid)
        for regime in regime_order:
            append_row("leave_one_regime_out", regime, valid[valid["regime"] != regime])
        if trend_col in panel.columns:
            trend = panel.loc[valid.index, trend_col]
            trend_valid = valid.assign(_trend=trend.to_numpy())
            trend_valid = trend_valid.dropna(subset=["_trend"])
            append_row("target_past_trend", "目标过去上涨", trend_valid[trend_valid["_trend"] > 0])
            append_row("target_past_trend", "目标过去非上涨", trend_valid[trend_valid["_trend"] <= 0])
    return pd.DataFrame(rows)


def summarize_significance(panel: pd.DataFrame, prefix: str, cfg: Config) -> pd.DataFrame:
    """Compare each regime with its leave-one-regime-out baseline."""
    rows: list[dict[str, object]] = []
    regime_order = ["增长扩散", "横盘钝化", "下降扩散", "混合"]
    for horizon in cfg.horizons:
        valid = _valid_outcome(panel, prefix, horizon)
        if valid.empty:
            continue
        ret_col = f"{prefix}_fwd_ret_{horizon}d"
        dd_col = f"{prefix}_fwd_dd_{horizon}d"
        for regime_idx, regime in enumerate(regime_order):
            regime_sample = valid[valid["regime"] == regime]
            baseline = valid[valid["regime"] != regime]
            for metric_idx, (metric, value_col, is_rate) in enumerate([
                ("return", ret_col, False),
                ("max_drawdown", dd_col, False),
                ("positive_rate", ret_col, True),
            ]):
                x = (regime_sample[value_col] > 0).astype(float) if is_rate else regime_sample[value_col]
                y = (baseline[value_col] > 0).astype(float) if is_rate else baseline[value_col]
                stats = _comparison_stats(x, y, seed=20260927 + regime_idx * 100 + horizon + metric_idx)
                rows.append({
                    "series": prefix,
                    "regime": regime,
                    "horizon": horizon,
                    "metric": metric,
                    "regime_obs": int(len(x)),
                    "baseline_type": "leave_one_regime_out",
                    "baseline_obs": int(len(y)),
                    "regime_mean": stats["regime_mean"],
                    "baseline_mean": stats["baseline_mean"],
                    "increment": stats["increment"],
                    "ci_low": stats["ci_low"],
                    "ci_high": stats["ci_high"],
                    "permutation_p": stats["permutation_p"],
                    "regime_positive_rate": float(x.mean()) if len(x) else math.nan,
                    "baseline_positive_rate": float(y.mean()) if len(y) else math.nan,
                    "positive_rate_diff": float(x.mean() - y.mean()) if len(x) and len(y) else math.nan,
                    "significant_05": stats["significant_05"],
                })
    return pd.DataFrame(rows)


def _stability_periods(valid: pd.DataFrame) -> list[tuple[str, str, pd.DataFrame]]:
    dates = pd.to_datetime(valid["trade_date"])
    periods: list[tuple[str, str, pd.DataFrame]] = []
    if len(valid):
        ordered = valid.sort_values("trade_date")
        split = max(1, len(ordered) // 2)
        first_half = ordered.iloc[:split]
        second_half = ordered.iloc[split:]
        if not first_half.empty:
            periods.append(("half", "前半样本", first_half))
        if not second_half.empty:
            periods.append(("half", "后半样本", second_half))
    for year, sample in valid.assign(_year=dates.dt.year).groupby("_year", sort=True):
        periods.append(("year", str(int(year)), sample.drop(columns="_year")))
    return periods


def summarize_stability(panel: pd.DataFrame, prefix: str, cfg: Config) -> pd.DataFrame:
    """Evaluate regime-vs-baseline increments across halves and calendar years."""
    rows: list[dict[str, object]] = []
    regime_order = ["增长扩散", "横盘钝化", "下降扩散", "混合"]
    for horizon in cfg.horizons:
        valid = _valid_outcome(panel, prefix, horizon)
        if valid.empty:
            continue
        ret_col = f"{prefix}_fwd_ret_{horizon}d"
        for period_type, period, sample in _stability_periods(valid):
            for regime_idx, regime in enumerate(regime_order):
                regime_sample = sample[sample["regime"] == regime]
                baseline = sample[sample["regime"] != regime]
                stats = _comparison_stats(
                    regime_sample[ret_col], baseline[ret_col],
                    seed=20260927 + horizon + regime_idx * 1000 + len(period),
                )
                rows.append({
                    "series": prefix,
                    "period_type": period_type,
                    "period": period,
                    "start_date": sample["trade_date"].min().date().isoformat(),
                    "end_date": sample["trade_date"].max().date().isoformat(),
                    "regime": regime,
                    "horizon": horizon,
                    "obs": int(len(regime_sample)),
                    "baseline_obs": int(len(baseline)),
                    "regime_mean_return": stats["regime_mean"],
                    "baseline_mean_return": stats["baseline_mean"],
                    "increment": stats["increment"],
                    "ci_low": stats["ci_low"],
                    "ci_high": stats["ci_high"],
                    "permutation_p": stats["permutation_p"],
                    "positive_rate_diff": (
                        float((regime_sample[ret_col] > 0).mean() - (baseline[ret_col] > 0).mean())
                        if len(regime_sample) and len(baseline) else math.nan
                    ),
                    "significant_05": stats["significant_05"],
                })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    keys = ["series", "period_type", "regime", "horizon"]
    consistency = out.groupby(keys, dropna=False).agg(
        periods_with_data=("obs", lambda x: int((x > 0).sum())),
        periods_with_baseline=("baseline_obs", lambda x: int((x > 0).sum())),
        positive_increment_periods=("increment", lambda x: int((x > 0).sum())),
        negative_increment_periods=("increment", lambda x: int((x < 0).sum())),
        significant_periods=("significant_05", "sum"),
        best_period_increment=("increment", "max"),
        worst_period_increment=("increment", "min"),
    ).reset_index()
    period_name_rows: list[dict[str, object]] = []
    for group_key, group in out.groupby(keys, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        row = dict(zip(keys, group_key))
        non_null = group.dropna(subset=["increment"])
        row["best_period"] = non_null.loc[non_null["increment"].idxmax(), "period"] if not non_null.empty else None
        row["worst_period"] = non_null.loc[non_null["increment"].idxmin(), "period"] if not non_null.empty else None
        period_name_rows.append(row)
    period_names = pd.DataFrame(period_name_rows)
    consistency = consistency.merge(period_names, on=keys, how="left")
    consistency["direction_consistency"] = consistency.apply(
        lambda row: (
            max(row["positive_increment_periods"], row["negative_increment_periods"])
            / (row["positive_increment_periods"] + row["negative_increment_periods"])
            if row["positive_increment_periods"] + row["negative_increment_periods"] else math.nan
        ), axis=1,
    )
    consistency["direction_stable"] = consistency["direction_consistency"] >= 0.75
    return out.merge(consistency, on=keys, how="left")


def stats_markdown_table(df: pd.DataFrame, columns: list[str], percent_columns: set[str] | None = None) -> str:
    out = df.loc[:, [col for col in columns if col in df.columns]].copy()
    percent_columns = percent_columns or set()
    for col in percent_columns:
        if col in out.columns:
            out[col] = out[col].map(lambda value: f"{value:.2%}" if pd.notna(value) else "—")
    for col in out.columns:
        if col in percent_columns:
            continue
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(lambda value: f"{value:.4f}" if pd.notna(value) else "—")
    return out.to_markdown(index=False)

def pct_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    non_pct = {"obs", "regime", "up_count", "sideways_count", "down_count", "active_count",
               "avg_up_count", "avg_sideways_count", "avg_down_count"}
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]) and col not in non_pct:
            out[col] = out[col] * 100
    return out


def chinese_summary_columns(columns: pd.Index) -> dict[str, str]:
    labels = {
        "regime": "扩散状态",
        "obs": "样本数",
        "avg_up_count": "平均上行数",
        "avg_sideways_count": "平均横盘数",
        "avg_down_count": "平均下跌数",
    }
    for col in columns:
        if col in labels:
            continue
        match = re.fullmatch(r"fwd_(\d+)d", col)
        if match:
            labels[col] = f"后{match.group(1)}日全样本平均收益(%)"
            continue
        match = re.fullmatch(r"fwd_(\d+)d_median", col)
        if match:
            labels[col] = f"后{match.group(1)}日收益中位数(%)"
            continue
        match = re.fullmatch(r"fwd_(\d+)d_p10", col)
        if match:
            labels[col] = f"后{match.group(1)}日收益P10(%)"
            continue
        match = re.fullmatch(r"fwd_(\d+)d_worst", col)
        if match:
            labels[col] = f"后{match.group(1)}日最差收益(%)"
            continue
        match = re.fullmatch(r"avg_fwd_(\d+)d_loss", col)
        if match:
            labels[col] = f"后{match.group(1)}日亏损样本平均收益(%)"
            continue
        match = re.fullmatch(r"p10_fwd_dd_(\d+)d", col)
        if match:
            labels[col] = f"后{match.group(1)}日最大回撤P10(%)"
            continue
        match = re.fullmatch(r"worst_fwd_dd_(\d+)d", col)
        if match:
            labels[col] = f"后{match.group(1)}日最差最大回撤(%)"
    return labels


def latest_detail_rows(detail: pd.DataFrame, state_window: int) -> pd.DataFrame:
    latest = detail.tail(1)
    rows = []
    for col in detail.columns:
        if col == "trade_date" or col.endswith("|state"):
            continue
        state_col = f"{col}|state"
        code, name = col.split("|", 1) if "|" in col else (col, col)
        rows.append({"标的": f"{name}({code})", f"{state_window}日收益(%)": latest[col].iloc[0], "状态": latest[state_col].iloc[0]})
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, column_labels: dict[str, str] | None = None) -> str:
    out = pct_table(df)
    if column_labels:
        out = out.rename(columns=column_labels)
    return out.to_markdown(index=False, floatfmt=".2f")


def write_report(
    cfg: Config,
    panel: pd.DataFrame,
    detail: pd.DataFrame,
    target_summary: pd.DataFrame,
    basket_summary: pd.DataFrame,
    target_baseline: pd.DataFrame,
    basket_baseline: pd.DataFrame,
    target_significance: pd.DataFrame,
    basket_significance: pd.DataFrame,
    target_stability: pd.DataFrame,
    basket_stability: pd.DataFrame,
    output_dir: Path,
) -> Path:
    latest = panel.dropna(subset=["target_close"]).iloc[-1]
    target_type_labels = {"index": "指数", "fund": "基金", "stock": "股票"}
    target_sig_view = target_significance[
        (target_significance["metric"].isin(["return", "max_drawdown"]))
    ].copy() if not target_significance.empty else target_significance
    stability_view = target_stability[target_stability["period_type"] == "half"].copy() if not target_stability.empty else target_stability
    basket_sig_view = basket_significance[
        (basket_significance["metric"].isin(["return", "max_drawdown"]))
    ].copy() if not basket_significance.empty else basket_significance
    basket_stability_view = basket_stability[basket_stability["period_type"] == "half"].copy() if not basket_stability.empty else basket_stability
    lines = [
        "# 核心标的状态扩散影响复盘",
        "",
        "## 口径",
        "",
        f"- 目标观察标的：`{cfg.target_code}` {cfg.target_name}（{target_type_labels.get(cfg.target_type, cfg.target_type)}）",
        f"- 核心标的池：{', '.join([f'{v}({k})' for k, v in cfg.stocks.items()])}",
        f"- 区间：`{cfg.analysis_start}` 至 `{cfg.end_date}`",
        f"- 状态窗口：`{cfg.state_window}` 个交易日；阈值：`±{cfg.band:.1%}`",
        f"- 多数扩散阈值：`{cfg.majority_count}` / `{len(cfg.stocks)}`",
        "- 统计同时给出全样本基准、剔除当前状态的 leave-one-regime-out 基准，以及目标自身过去趋势基准；显著性使用置换检验，区间使用 bootstrap 95% CI。",
        "- 样本不足或无法建立对照时，表格保留样本数并以 `—` 表示，不把缺失结果解释成“不显著”。",
        "",
        "## 最新状态",
        "",
        f"- 最新交易日：`{latest['trade_date'].date()}`",
        f"- 增长/横盘/下降数量：`{int(latest['up_count'])}` / `{int(latest['sideways_count'])}` / `{int(latest['down_count'])}`",
        f"- 扩散状态：`{latest['regime']}`",
        f"- 核心篮子胜率：`{latest[f'core_win_rate_{cfg.state_window}d']:.1%}`",
        "",
        "### 最新核心标的状态",
        "",
        markdown_table(latest_detail_rows(detail, cfg.state_window)),
        "",
        "## 目标标的：按扩散状态",
        "",
        markdown_table(target_summary, chinese_summary_columns(target_summary.columns)),
        "",
        "## 核心等权篮子：按扩散状态",
        "",
        markdown_table(basket_summary, chinese_summary_columns(basket_summary.columns)),
        "",
        "## 基准比较",
        "",
        "基准不是把某个状态与包含它的全样本机械比较：主要增量采用剔除当前状态的 leave-one-regime-out 基准；目标自身过去上涨/非上涨仅作趋势匹配的描述性基准。完整结果见 `baseline_summary.csv`。",
        "",
        "### 目标标的基准",
        "",
        stats_markdown_table(
            target_baseline,
            ["horizon", "baseline_type", "regime", "obs", "mean_return", "positive_rate", "mean_max_drawdown", "p10_return", "p10_max_drawdown"],
            {"mean_return", "positive_rate", "mean_max_drawdown", "p10_return", "p10_max_drawdown"},
        ) if not target_baseline.empty else "暂无有效基准样本。",
        "",
        "### 核心等权篮子基准（摘要）",
        "",
        stats_markdown_table(
            basket_baseline,
            ["horizon", "baseline_type", "regime", "obs", "mean_return", "positive_rate", "mean_max_drawdown"],
            {"mean_return", "positive_rate", "mean_max_drawdown"},
        ) if not basket_baseline.empty else "暂无有效基准样本。",
        "",
        "## 显著性判断",
        "",
        "`increment` 为当前扩散状态相对 leave-one-regime-out 基准的差值；收益和胜率增量为正通常更好，最大回撤增量为正通常表示回撤较浅。p 值为双侧置换检验，不能替代经济意义和样本审计。完整结果见 `regime_significance.csv`。",
        "",
        stats_markdown_table(
            target_sig_view.head(48),
            ["regime", "horizon", "metric", "regime_obs", "baseline_obs", "regime_mean", "baseline_mean", "increment", "ci_low", "ci_high", "permutation_p", "significant_05"],
            {"regime_mean", "baseline_mean", "increment", "ci_low", "ci_high"},
        ) if not target_sig_view.empty else "暂无可比较的显著性样本。",
        "",
        "### 核心等权篮子显著性（摘要）",
        "",
        stats_markdown_table(
            basket_sig_view.head(24),
            ["regime", "horizon", "metric", "regime_obs", "baseline_obs", "regime_mean", "baseline_mean", "increment", "permutation_p", "significant_05"],
            {"regime_mean", "baseline_mean", "increment"},
        ) if not basket_sig_view.empty else "暂无可比较的显著性样本。",
        "",
        "## 稳定性判断",
        "",
        "稳定性按前半/后半样本和自然年度重复比较。`direction_consistency` 是增量方向一致的子阶段比例；`direction_stable=True` 仅表示方向在至少 75% 的有方向子阶段一致，不代表因果已被证明。完整结果见 `regime_stability.csv`。",
        "",
        stats_markdown_table(
            stability_view.head(48),
            ["period", "regime", "horizon", "obs", "baseline_obs", "regime_mean_return", "baseline_mean_return", "increment", "permutation_p", "significant_05", "best_period", "worst_period", "best_period_increment", "worst_period_increment", "direction_consistency", "direction_stable"],
            {"regime_mean_return", "baseline_mean_return", "increment", "direction_consistency"},
        ) if not stability_view.empty else "暂无可比较的稳定性样本。",
        "",
        "### 核心等权篮子稳定性（摘要）",
        "",
        stats_markdown_table(
            basket_stability_view.head(24),
            ["period", "regime", "horizon", "obs", "baseline_obs", "increment", "permutation_p", "significant_05", "direction_consistency", "direction_stable"],
            {"increment", "direction_consistency"},
        ) if not basket_stability_view.empty else "暂无可比较的稳定性样本。",
        "",
        "## 结论降级规则",
        "",
        "- 极端状态样本少、leave-one-regime-out 对照为空、或只在单一年度出现时，不输出稳定的历史优势结论。",
        "- 显著性只描述当前样本下的差异；若前后半样本方向相反、CI跨零或年度方向不一致，应降级为阶段性现象。",
        "- 目标与核心篮子结果不一致时，优先保留差异并检查权重、同步交易日和目标构成，不强行合并成单一结论。",
        "",
    ]
    path = output_dir / "core_stock_sector_impact_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    cfg = parse_args()
    token = ensure_token()
    ts.set_token(token)
    pro = ts.pro_api(token)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = cfg.output_dir / "cache"

    stock_frames = [load_stock_daily(code, name, cfg, cache_dir) for code, name in cfg.stocks.items()]
    target = load_target_daily(pro, cfg, cache_dir)
    wide = build_wide(stock_frames)
    panel, detail = build_panel(wide, target, cfg)

    target_summary = summarize(panel, "target", cfg)
    basket_summary = summarize(panel, "core_basket", cfg)
    target_baseline = summarize_baselines(panel, "target", cfg)
    basket_baseline = summarize_baselines(panel, "core_basket", cfg)
    target_significance = summarize_significance(panel, "target", cfg)
    basket_significance = summarize_significance(panel, "core_basket", cfg)
    target_stability = summarize_stability(panel, "target", cfg)
    basket_stability = summarize_stability(panel, "core_basket", cfg)
    panel.to_csv(cfg.output_dir / "daily_panel.csv", index=False)
    detail.to_csv(cfg.output_dir / "stock_state_detail.csv", index=False)
    target_summary.to_csv(cfg.output_dir / "summary_target_by_regime.csv", index=False)
    basket_summary.to_csv(cfg.output_dir / "summary_core_basket_by_regime.csv", index=False)
    pd.concat([target_baseline, basket_baseline], ignore_index=True).to_csv(
        cfg.output_dir / "baseline_summary.csv", index=False
    )
    pd.concat([target_significance, basket_significance], ignore_index=True).to_csv(
        cfg.output_dir / "regime_significance.csv", index=False
    )
    pd.concat([target_stability, basket_stability], ignore_index=True).to_csv(
        cfg.output_dir / "regime_stability.csv", index=False
    )
    for count_col in ["up_count", "sideways_count", "down_count"]:
        summarize_by_count(panel, count_col, "target", cfg).to_csv(
            cfg.output_dir / f"summary_target_by_{count_col}.csv", index=False
        )
        summarize_by_count(panel, count_col, "core_basket", cfg).to_csv(
            cfg.output_dir / f"summary_core_basket_by_{count_col}.csv", index=False
        )
    report = write_report(
        cfg, panel, detail, target_summary, basket_summary,
        target_baseline, basket_baseline, target_significance, basket_significance,
        target_stability, basket_stability, cfg.output_dir,
    )
    (cfg.output_dir / "run_meta.json").write_text(
        json.dumps({"run_at": datetime.now().isoformat(timespec="seconds"), "config": cfg.__dict__ | {"output_dir": str(cfg.output_dir)}}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"report={report.resolve()}")
    print(f"panel={(cfg.output_dir / 'daily_panel.csv').resolve()}")


if __name__ == "__main__":
    main()
