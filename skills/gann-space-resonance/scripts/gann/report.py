from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


def verdict_label(row: pd.Series) -> str:
    n = int(row.get("trials", 0))
    excess = float(row.get("excess", float("nan")))
    p_adjusted = float(row.get("p_adjusted", float("nan")))
    if n < 20:
        return "样本不足"
    if not math.isfinite(excess):
        return "无法判断"
    if p_adjusted < 0.01 and excess >= 0.10 and n >= 60:
        return "有效"
    if p_adjusted < 0.05 and excess >= 0.05:
        return "有苗头待扩样"
    if excess <= 0:
        return "无超额降级"
    return "未达显著"


def write_markdown_reports(
    output_dir: Path,
    audit: dict,
    stats: pd.DataFrame,
    event_summary: pd.DataFrame,
    current_levels: pd.DataFrame,
    assumptions: list[str],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stats = stats.copy()
    stats["verdict"] = stats.apply(verdict_label, axis=1)

    lines = [
        "# 上证指数近5年江恩时间-空间统计检验",
        "",
        "> 本项目为交易方法论的统计验证研究，不构成任何证券买卖建议，不预示未来表现。",
        "",
        "## 数据审计",
        "",
        f"- 区间：{audit['start']} 至 {audit['end']}，共 {audit['rows']} 个交易日。",
        f"- 重复日期：{audit['duplicate_dates']}；异常 OHLC：{audit['invalid_ohlc_rows']}；审计通过：{audit['passed']}。",
        "",
        "## 机械口径与人工裁决",
        "",
    ]
    lines.extend(f"- {item}" for item in assumptions)
    lines.extend(
        [
            "",
            "## 拐点命中相对随机基线",
            "",
            "主结论看超额，不以裸命中率作为有效证据。p 值为单侧二项检验，并对同族检验做 Bonferroni 校正。",
            "",
            "|维度|工具|方向|容差|样本|命中率|基线|超额|p值|校正p|裁决|",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in stats.itertuples(index=False):
        lines.append(
            f"|{row.dimension}|{row.tool}|{row.direction}|{row.tolerance:.1%}|{row.trials}|"
            f"{row.hit_rate:.1%}|{row.baseline:.1%}|{row.excess:+.1%}|{row.p_value:.3f}|"
            f"{row.p_adjusted:.3f}|{row.verdict}|"
        )

    lines.extend(["", "## 价位实际触碰后的反应", ""])
    if event_summary.empty:
        lines.append("没有满足机械入带条件且拥有完整未来观察窗的事件。")
    else:
        lines.extend(
            [
                "形成支撑/压力定义为：从带外进入指数±1%价位带后，在观察期内未收盘穿越另一侧，同时至少产生1%的有利运动。",
                "",
                "|工具|方向|窗口|事件数|成功率|匹配基线|超额|校正p|平均有利波动|平均不利波动|",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in event_summary.itertuples(index=False):
            lines.append(
                f"|{row.tool}|{row.direction}|{row.horizon}日|{row.events}|{row.success_rate:.1%}|"
                f"{row.baseline:.1%}|{row.excess:+.1%}|{row.p_adjusted:.3f}|"
                f"{row.mean_favorable:.1%}|{row.mean_adverse:.1%}|"
            )

    lines.extend(["", "## 最新候选支撑与压力", ""])
    if current_levels.empty:
        lines.append("暂无可用候选位。")
    else:
        lines.extend(["|性质|成员区间|中心点位|距最新收盘|来源数|来源|", "|---|---:|---:|---:|---:|---|"])
        for row in current_levels.itertuples(index=False):
            lines.append(
                f"|{row.kind}|{row.zone_lower:.2f}-{row.zone_upper:.2f}|{row.level:.2f}|"
                f"{row.distance:+.2%}|{row.source_count}|{row.sources}|"
            )

    lines.extend(
        [
            "",
            "## 合规声明",
            "",
            "本项目为交易方法论的统计验证研究。所有“命中/有效”均为历史数据统计意义上的表述，不构成任何证券的买卖建议，不预示未来表现。",
            "",
        ]
    )
    (output_dir / "hit_report.md").write_text("\n".join(lines), encoding="utf-8")

    verdict_lines = [
        "# 工具裁决",
        "",
        "> 本项目为交易方法论的统计验证研究，不构成任何证券买卖建议。",
        "",
    ]
    for row in stats.itertuples(index=False):
        verdict_lines.append(
            f"- **{row.dimension}/{row.tool}/{row.direction}**：{row.verdict}。"
            f"命中 {row.successes}/{row.trials}（{row.hit_rate:.1%}），基线 {row.baseline:.1%}，"
            f"超额 {row.excess:+.1%}，校正 p={row.p_adjusted:.3f}。"
        )
    verdict_lines.extend(
        [
            "",
            "本项目为交易方法论的统计验证研究。所有结果不构成任何证券的买卖建议，不预示未来表现。",
            "",
        ]
    )
    (output_dir / "verdict.md").write_text("\n".join(verdict_lines), encoding="utf-8")
