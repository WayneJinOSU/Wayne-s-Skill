#!/usr/bin/env python3
"""Generate an auditable weekly price/time scenario report from weekly OHLCV and reviewed events."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


def load_weekly(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    date_column = "week_end" if "week_end" in frame.columns else "trade_date"
    required = {date_column, "open", "high", "low", "close"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Weekly file missing columns: {sorted(missing)}")
    frame = frame.rename(columns={date_column: "week_end"}).copy()
    frame["week_end"] = pd.to_datetime(frame["week_end"])
    for col in ("open", "high", "low", "close"):
        frame[col] = pd.to_numeric(frame[col], errors="raise")
    frame = frame.sort_values("week_end").drop_duplicates("week_end")
    if len(frame) < 60:
        raise ValueError("At least 60 weekly rows are required.")
    return frame.reset_index(drop=True)


def confirmed_pivots(frame: pd.DataFrame, window: int = 3) -> list[dict]:
    pivots: list[dict] = []
    # A pivot is only known after `window` later bars; the last window is intentionally excluded.
    for i in range(window, len(frame) - window):
        lows = frame.low.iloc[i - window:i + window + 1]
        highs = frame.high.iloc[i - window:i + window + 1]
        if frame.low.iloc[i] == lows.min() and (lows == frame.low.iloc[i]).sum() == 1:
            pivots.append({"index": i, "date": frame.week_end.iloc[i], "kind": "low", "price": float(frame.low.iloc[i])})
        elif frame.high.iloc[i] == highs.max() and (highs == frame.high.iloc[i]).sum() == 1:
            pivots.append({"index": i, "date": frame.week_end.iloc[i], "kind": "high", "price": float(frame.high.iloc[i])})
    pivots.sort(key=lambda x: x["index"])
    filtered: list[dict] = []
    for pivot in pivots:
        if not filtered or pivot["kind"] != filtered[-1]["kind"]:
            filtered.append(pivot)
        elif (pivot["kind"] == "high" and pivot["price"] > filtered[-1]["price"]) or (pivot["kind"] == "low" and pivot["price"] < filtered[-1]["price"]):
            filtered[-1] = pivot
    return filtered


def last_completed_correction(pivots: list[dict], direction: str) -> int | None:
    needed = ("high", "low") if direction == "up" else ("low", "high")
    matches = [(a, b) for a, b in zip(pivots, pivots[1:]) if (a["kind"], b["kind"]) == needed]
    if not matches:
        return None
    a, b = matches[-1]
    return max(1, b["index"] - a["index"])


def abc_down_candidate(pivots: list[dict], latest_close: float) -> dict | None:
    """Return the latest confirmed high-low-high A-B-C-down setup, if still actionable.

    This deliberately identifies a correction candidate rather than fabricating an
    impulse-wave 1–5 count from sparse weekly pivots.
    """
    if len(pivots) < 4:
        return None
    prior, start, a_low, b_high = pivots[-4:]
    if (prior["kind"], start["kind"], a_low["kind"], b_high["kind"]) != ("low", "high", "low", "high"):
        return None
    a_length = start["price"] - a_low["price"]
    b_length = b_high["price"] - a_low["price"]
    if a_length <= 0 or b_high["price"] >= start["price"] or latest_close >= b_high["price"]:
        return None
    return {
        "start": start,
        "prior_low": prior,
        "a_low": a_low,
        "b_high": b_high,
        "a_length": a_length,
        "b_retrace": b_length / a_length,
        "a_duration": max(1, a_low["index"] - start["index"]),
        "c_0618": b_high["price"] - a_length * 0.618,
        "c_1000": b_high["price"] - a_length,
        "c_1618": b_high["price"] - a_length * 1.618,
    }


def leader_context(path: str | None) -> tuple[float, list[str]]:
    if not path:
        return 0.0, ["- 未提供市场总龙头篮子；本期浪型置信度未获龙头验证。"]
    leaders = pd.read_csv(path)
    required = {"name", "role", "state", "ret_4w", "above_ema13", "above_ema34"}
    missing = required.difference(leaders.columns)
    if missing:
        return 0.0, [f"- 龙头数据缺少字段 {sorted(missing)}；未纳入验证。"]
    if leaders.empty:
        return 0.0, ["- 龙头篮子为空；未纳入验证。"]
    leaders["above_ema13"] = leaders["above_ema13"].astype(str).str.lower().eq("true")
    leaders["above_ema34"] = leaders["above_ema34"].astype(str).str.lower().eq("true")
    leaders["ret_4w"] = pd.to_numeric(leaders["ret_4w"], errors="coerce")
    strong_share = float((leaders.above_ema13 & leaders.above_ema34).mean())
    weak_share = float((~leaders.above_ema13 & ~leaders.above_ema34).mean())
    median_return = float(leaders.ret_4w.median())
    score = 1.0 if strong_share >= 0.6 else -1.0 if weak_share >= 0.6 else 0.0
    state_lines = [
        f"- 龙头篮子：{len(leaders)}只；{strong_share:.0%}位于EMA13和EMA34之上，{weak_share:.0%}位于两条均线之下；4周收益中位数 {median_return:+.1%}。",
    ]
    state_label = {
        "strong": "趋势强势",
        "above_trend_short_pullback": "趋势上方、短线回撤",
        "weak": "趋势弱势",
        "below_trend_rebound": "趋势下方、短线反弹",
        "mixed": "均线分歧",
    }
    for row in leaders.sort_values(["role", "name"]).head(8).itertuples():
        state_lines.append(f"- {row.name}（{row.role}）：{state_label.get(row.state, row.state)}，4周 {row.ret_4w:+.1%}。")
    return score, state_lines


def parent_context(path: str | None) -> str:
    if not path:
        raise ValueError("--parent-context is required; it must explain parent waves 1–5 for every index report.")
    content = Path(path).read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError("--parent-context is empty; explain parent waves 1–5, including unfinished waves.")
    missing = [str(wave) for wave in range(1, 6) if not re.search(rf"{wave}\s*浪", content)]
    if missing:
        raise ValueError(f"--parent-context must explicitly cover parent waves 1–5; missing: {', '.join(missing)}浪")
    return content


def event_context(path: str | None, as_of: pd.Timestamp) -> tuple[float, list[str]]:
    if not path:
        return 0.0, []
    events = pd.read_csv(path)
    if events.empty or "event_score" not in events:
        return 0.0, []
    # Normalise source time zones before comparing with date-only weekly bars.
    events["published_at"] = pd.to_datetime(events["published_at"], utc=True).dt.tz_localize(None)
    events["effective_from"] = pd.to_datetime(events["effective_from"], utc=True).dt.tz_localize(None)
    events["effective_to"] = pd.to_datetime(events["effective_to"], utc=True).dt.tz_localize(None)
    active = events[(events.published_at <= as_of) & (events.effective_from <= as_of + pd.Timedelta(days=30)) & (events.effective_to >= as_of - pd.Timedelta(days=30))].copy()
    if active.empty:
        return 0.0, []
    raw_score = float(active.event_score.clip(-1, 1).sum())
    score = max(-1.0, min(1.0, raw_score))
    lines = [f"- {row.title}（{row.event_type}/{row.status}，事件分值 {row.event_score:+.2f}）" for row in active.sort_values("published_at", ascending=False).head(5).itertuples()]
    return score, lines


def fmt(value: float) -> str:
    return f"{value:,.0f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weekly", required=True)
    parser.add_argument("--events")
    parser.add_argument("--leaders")
    parser.add_argument("--parent-context", required=True, help="reviewed Markdown defining parent waves 1–5, including unfinished-wave status")
    parser.add_argument("--parent-retrace-low", type=float, help="lower edge of the parent-wave correction target band")
    parser.add_argument("--parent-hard-invalidation", type=float, help="parent-wave price level that invalidates the local count")
    parser.add_argument("--index-name", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    frame = load_weekly(args.weekly)
    frame["ema13"] = frame.close.ewm(span=13, adjust=False).mean()
    frame["ema34"] = frame.close.ewm(span=34, adjust=False).mean()
    latest = frame.iloc[-1]
    trend = "up" if latest.ema13 > latest.ema34 and latest.close >= latest.ema13 else "down" if latest.ema13 < latest.ema34 and latest.close <= latest.ema13 else "range"
    pivots = confirmed_pivots(frame)
    if len(pivots) < 4:
        raise ValueError("Too few confirmed pivots; inspect data or extend history.")

    abc = abc_down_candidate(pivots, float(latest.close))
    if abc:
        core_half_width = abc["a_length"] * 0.08
        core = sorted([abc["c_1000"] - core_half_width, abc["c_1000"] + core_half_width])
        extended = sorted([abc["c_1618"], abc["c_0618"]])
        if args.parent_retrace_low is not None:
            extended[0] = args.parent_retrace_low
            extended = sorted(extended)
        invalidation = abc["start"]["price"]
        confirmation = f"周线收盘跌破A浪低点 {fmt(abc['a_low']['price'])}"
        label = "A-B-C下行调整：C浪推进"
        alternative = "B浪未结束或平台上沿重测"
        alternative_confirmation = f"周线收盘站上B浪高点 {fmt(abc['b_high']['price'])}"
        reference_duration = abc["a_duration"]
        wave_count = f"""## 波浪主计数

- **A浪**：{abc['start']['date'].date()} 的 {fmt(abc['start']['price'])} 下行至 {abc['a_low']['date'].date()} 的 {fmt(abc['a_low']['price'])}，幅度 {fmt(abc['a_length'])} 点，历时 {abc['a_duration']} 周。
- **B浪**：从 {fmt(abc['a_low']['price'])} 反弹至 {abc['b_high']['date'].date()} 的 {fmt(abc['b_high']['price'])}，回撤A浪 {abc['b_retrace']:.1%}；B浪没有越过A浪起点 {fmt(abc['start']['price'])}，因此A-B-C下行调整的基本约束仍成立。
- **C浪主预测**：B浪高点后最新周线收于 {fmt(latest.close)}；本模型预判C浪将向等长目标 {fmt(abc['c_1000'])} 推进。周线收盘跌破A浪低点 {fmt(abc['a_low']['price'])} 将强化该预判。
- **C浪目标**：0.618×A为 {fmt(abc['c_0618'])}，1.000×A为 {fmt(abc['c_1000'])}，1.618×A为 {fmt(abc['c_1618'])}。核心区围绕等长C浪设置为 {fmt(core[0])}–{fmt(core[1])}。
- **它调整的是谁**：这组A-B-C直接调整的是 {abc['prior_low']['date'].date()} 的 {fmt(abc['prior_low']['price'])} 上行至 {abc['start']['date'].date()} 的 {fmt(abc['start']['price'])} 的最近一段上行走势；在本报告的级别定义中，它是“该上行段之后的低一级周线调整”。
- **局部结构的限制**：单凭最近拐点，不能把当前调整直接称为2浪或4浪；必须由下方“上级别计数”证明 {fmt(abc['start']['price'])} 是父级3浪终点。若它实际是父级5浪终点，则当前A-B-C会是更大级别调整的A浪起始，而不是4浪。
"""
    elif trend == "up":
        base = next((p for p in reversed(pivots) if p["kind"] == "low"), None)
        extreme = max(float(frame.high.iloc[base["index"]:].max()), float(latest.close)) if base else float(frame.high.max())
        amplitude = extreme - base["price"] if base else float(frame.close.max() - frame.close.min())
        core = sorted([extreme - amplitude * 0.382, extreme - amplitude * 0.236])
        extended = sorted([extreme - amplitude * 0.50, extreme - amplitude * 0.236])
        invalidation = extreme - amplitude * 0.618
        label = "上行结构中的4浪调整"
        alternative = "高位平台或延续上行"
        confirmation = "周线收盘在核心区出现止跌/转强结构"
        alternative_confirmation = "周线持续站稳/跌破EMA13并伴随宽度确认"
        wave_count = "## 波浪主计数\n\n- 当前主路径为上行结构中的调整后延续；1–5细分按后续拐点更新。\n"
    elif trend == "down":
        base = next((p for p in reversed(pivots) if p["kind"] == "high"), None)
        extreme = min(float(frame.low.iloc[base["index"]:].min()), float(latest.close)) if base else float(frame.low.min())
        amplitude = base["price"] - extreme if base else float(frame.close.max() - frame.close.min())
        core = sorted([extreme + amplitude * 0.236, extreme + amplitude * 0.382])
        extended = sorted([extreme + amplitude * 0.236, extreme + amplitude * 0.50])
        invalidation = extreme + amplitude * 0.618
        label = "下行结构中的反弹/修正"
        alternative = "弱反弹后延续下行"
        confirmation = "周线收盘在核心区出现反弹/转弱结构"
        alternative_confirmation = "周线持续站稳/跌破EMA13并伴随宽度确认"
        wave_count = "## 波浪主计数\n\n- 当前主路径为下行结构中的反弹修正；1–5细分按后续拐点更新。\n"
    else:
        amplitude = float(frame.high.iloc[-26:].max() - frame.low.iloc[-26:].min())
        center = float(latest.close)
        core = [center - amplitude * 0.191, center + amplitude * 0.191]
        extended = [center - amplitude * 0.309, center + amplitude * 0.309]
        invalidation = center - amplitude * 0.5
        label = "周线平台整理"
        alternative = "平台突破后形成方向性结构"
        confirmation = "周线收盘在核心区出现止跌/转强结构"
        alternative_confirmation = "周线持续站稳/跌破EMA13并伴随宽度确认"
        wave_count = "## 波浪主计数\n\n- 当前主路径为周线平台后的方向选择；突破或破位将决定下一段主浪。\n"

    if not abc:
        reference_duration = last_completed_correction(pivots, trend if trend in {"up", "down"} else "up") or 4
    low_weeks = max(2, round(reference_duration * 0.618))
    high_weeks = min(12, max(low_weeks + 1, round(reference_duration * 1.618)))
    event_score, event_lines = event_context(args.events, latest.week_end)
    leadership_score, leadership_lines = leader_context(args.leaders)
    parent_count = parent_context(args.parent_context)
    if abc and args.parent_context:
        label = "大级别4浪内的A-B-C调整：C浪推进"
    invalidation_display = fmt(invalidation)
    if abc and args.parent_hard_invalidation is not None:
        invalidation_display = f"局部 {fmt(invalidation)}；父级 {fmt(args.parent_hard_invalidation)}"
        wave_count += (
            f"\n- **父级限制**：局部1.618×A的机械延长位 {fmt(abc['c_1618'])} "
            f"低于父级4浪硬失效位 {fmt(args.parent_hard_invalidation)}，不作为正常C浪目标；"
            f"若价格有效进入 {fmt(args.parent_hard_invalidation)} 以下，应放弃4浪主计数并重数。\n"
        )
    if abc:
        primary_forecast = (
            f"**主预测：{args.index_name}将在未来 {low_weeks}–{high_weeks} 周完成当前调整，"
            f"C浪终点看向 {fmt((core[0] + core[1]) / 2)} 附近，核心区 {fmt(core[0])}–{fmt(core[1])}。**"
        )
    elif trend == "up":
        primary_forecast = f"**主预测：{args.index_name}维持周线向上结构，优先沿趋势推进；关注核心回撤区 {fmt(core[0])}–{fmt(core[1])} 的承接。**"
    elif trend == "down":
        primary_forecast = f"**主预测：{args.index_name}维持周线向下结构，反弹以修正看待，观察核心反弹区 {fmt(core[0])}–{fmt(core[1])}。**"
    else:
        primary_forecast = f"**主预测：{args.index_name}维持周线平台，等待方向选择；核心运行区 {fmt(core[0])}–{fmt(core[1])}。**"
    pivot_text = "；".join(f"{p['date'].date()} {p['kind']} {fmt(p['price'])}" for p in pivots[-6:])
    events_text = "\n".join(event_lines) if event_lines else "- 无处于有效窗口、且已在账本中核验的事件。"
    report = f"""# {args.index_name} 周线预判

数据截至：{latest.week_end.date()}（周线收盘）  
价格数据：`{args.weekly}`

{primary_forecast}

| 路径 | 当前结构 | 时间窗口 | 目标/运行区 | 验证 | 改判 |
|---|---|---:|---:|---|---|
| 主预测 | {label} | 未来 {low_weeks}–{high_weeks} 周 | {fmt(core[0])}–{fmt(core[1])} | {confirmation} | {invalidation_display} |
| 备选路径 | {alternative} | 未来 2–{high_weeks} 周 | 以周线EMA13（{fmt(latest.ema13)}）为观察轴 | {alternative_confirmation} | 以主预测改判位重估 |

{wave_count}

## 上级别计数

{parent_count}

## 结构证据

- 最新收盘 {fmt(latest.close)}；EMA13 {fmt(latest.ema13)}；EMA34 {fmt(latest.ema34)}；系统趋势状态：`{trend}`。
- 最近已确认的候选拐点：{pivot_text}。
- 价格区间由最近周线摆动的 23.6%、38.2% 与 50% 回撤构成；它是价格带，不是单一点位预测。
- 时间窗以最近可识别调整时长（{reference_duration} 周）按 0.618× 至 1.618×估计。

## 已核验事件上下文

30日事件合计分值：{event_score:+.2f}。该分值至多调整置信度一个档位，不改变价格区或失效位。

{events_text}

## 市场总龙头验证

龙头确认分值：{leadership_score:+.2f}。该分值只调整浪型置信度，不替代指数确认/失效位。

{"\n".join(leadership_lines)}

## 判断纪律

- 浪型推演以已确认周线拐点为基础；价格触发改判时，下一期报告立即采用新主预测。
- IPO、政策与事件只使用可核验的原始来源，并分开讨论资金供给、估值锚、产业预期与风险偏好。
"""
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
