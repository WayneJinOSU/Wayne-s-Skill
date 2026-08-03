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
    values = close.to_numpy()
    result = np.full(len(close), np.nan)
    for i in range(len(close)):
        end = min(i + horizon, len(close) - 1)
        if i + 1 > end:
            continue
        result[i] = values[i + 1 : end + 1].min() / values[i] - 1
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


def write_report(cfg: Config, panel: pd.DataFrame, detail: pd.DataFrame, target_summary: pd.DataFrame,
                 basket_summary: pd.DataFrame, output_dir: Path) -> Path:
    latest = panel.dropna(subset=["target_close"]).iloc[-1]
    target_type_labels = {"index": "指数", "fund": "基金", "stock": "股票"}
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
        f"- 统计口径：`后N日全样本平均收益`包含全部有效样本；`后N日亏损样本平均收益`只包含后N日收益为负的样本。",
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
    panel.to_csv(cfg.output_dir / "daily_panel.csv", index=False)
    detail.to_csv(cfg.output_dir / "stock_state_detail.csv", index=False)
    target_summary.to_csv(cfg.output_dir / "summary_target_by_regime.csv", index=False)
    basket_summary.to_csv(cfg.output_dir / "summary_core_basket_by_regime.csv", index=False)
    for count_col in ["up_count", "sideways_count", "down_count"]:
        summarize_by_count(panel, count_col, "target", cfg).to_csv(
            cfg.output_dir / f"summary_target_by_{count_col}.csv", index=False
        )
        summarize_by_count(panel, count_col, "core_basket", cfg).to_csv(
            cfg.output_dir / f"summary_core_basket_by_{count_col}.csv", index=False
        )
    report = write_report(cfg, panel, detail, target_summary, basket_summary, cfg.output_dir)
    (cfg.output_dir / "run_meta.json").write_text(
        json.dumps({"run_at": datetime.now().isoformat(timespec="seconds"), "config": cfg.__dict__ | {"output_dir": str(cfg.output_dir)}}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"report={report.resolve()}")
    print(f"panel={(cfg.output_dir / 'daily_panel.csv').resolve()}")


if __name__ == "__main__":
    main()
