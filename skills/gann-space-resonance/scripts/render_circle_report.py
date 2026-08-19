#!/usr/bin/env python3
"""Render a self-contained Gann spiral plus a concise evidence-aware narrative."""

from __future__ import annotations

import argparse
import html
import math
from pathlib import Path

import pandas as pd


def point(turn: float, max_turn: float, cx: float = 350, cy: float = 350, outer: float = 292):
    radius = 18 + (outer - 18) * turn / max_turn
    angle = -math.pi / 2 + 2 * math.pi * turn
    return cx + math.cos(angle) * radius, cy + math.sin(angle) * radius


def spiral_path(start: float, end: float, max_turn: float, steps: int = 80) -> str:
    parts = []
    for index in range(steps + 1):
        turn = start + (end - start) * index / steps
        x, y = point(turn, max_turn)
        parts.append(("M" if index == 0 else "L") + f"{x:.2f},{y:.2f}")
    return "".join(parts)


def fmt_zone(row) -> str:
    return f"{row.zone_lower:.2f}-{row.zone_upper:.2f}（中心 {row.level:.2f}）"


def render_markdown(markdown_text: str) -> str:
    """Render a reviewed local Markdown wave report, with a dependency-free fallback."""
    try:
        import mistune

        renderer = mistune.create_markdown(plugins=["table"])
        return renderer(markdown_text)
    except ImportError:
        try:
            from markdown_it import MarkdownIt

            return MarkdownIt("commonmark", {"html": False}).enable("table").render(markdown_text)
        except ImportError:
            return f'<pre class="markdown-fallback">{html.escape(markdown_text)}</pre>'


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the Gann circle and written interpretation")
    parser.add_argument("--results", type=Path, required=True, help="Directory created by run_index_study.py")
    parser.add_argument("--symbol", default="上证指数")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--wave-report",
        type=Path,
        default=None,
        help="Reviewed Markdown containing parent 1-5 count, current wave and 4-12 week scenarios",
    )
    args = parser.parse_args()
    output_dir = args.output or args.results
    output_dir.mkdir(parents=True, exist_ok=True)

    levels = pd.read_csv(args.results / "current_levels.csv")
    pivots = pd.read_csv(args.results / "turning_points.csv", parse_dates=["pivot_date", "confirm_date"])
    stats = pd.read_csv(args.results / "statistical_results.csv")
    if levels.empty or pivots.empty:
        raise ValueError("current_levels.csv and turning_points.csv must be non-empty")

    anchor_row = pivots.loc[pivots["type"] == "L"].sort_values("price").iloc[0]
    anchor = float(anchor_row["price"])
    anchor_date = pd.Timestamp(anchor_row["pivot_date"]).strftime("%Y-%m-%d")
    latest_close = float(levels.iloc[0]["level"] / (1.0 + levels.iloc[0]["distance"]))
    as_of = str(levels.iloc[0]["as_of"])
    anchor_root = math.sqrt(anchor)

    def turns(price: float) -> float:
        return (math.sqrt(float(price)) - anchor_root) / 2.0

    max_price = max(float(levels["zone_upper"].max()) * 1.04, latest_close * 1.08)
    max_turn = max(turns(max_price), 1.0)
    spiral = spiral_path(0, max_turn, max_turn, 900)

    spokes = []
    for degree in range(0, 360, 45):
        angle = -math.pi / 2 + math.radians(degree)
        x2, y2 = 350 + math.cos(angle) * 292, 350 + math.sin(angle) * 292
        spokes.append(
            f'<line x1="350" y1="350" x2="{x2:.2f}" y2="{y2:.2f}" class="spoke {"major" if degree % 90 == 0 else ""}"/>'
        )
        lx, ly = 350 + math.cos(angle) * 313, 350 + math.sin(angle) * 313
        spokes.append(f'<text x="{lx:.2f}" y="{ly + 4:.2f}" text-anchor="middle" class="degree">{degree}°</text>')

    rings = [f'<circle cx="350" cy="350" r="{18 + (292 - 18) * turn / max_turn:.2f}" class="ring"/>' for turn in range(1, math.floor(max_turn) + 1)]
    square_marks = []
    turn = 0.0
    while turn <= max_turn:
        x, y = point(turn, max_turn)
        price = (anchor_root + 2 * turn) ** 2
        square_marks.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.7" class="square-mark"><title>{price:.2f}点 · {(turn % 1) * 360:.0f}°</title></circle>')
        turn += 0.25

    zone_marks = []
    for row in levels.itertuples(index=False):
        kind = "support" if row.kind == "支撑" else "resistance"
        start, end = turns(row.zone_lower), turns(row.zone_upper)
        path = spiral_path(start, end, max_turn, 50)
        center_turn = turns(row.level)
        x, y = point(center_turn, max_turn)
        angle = -math.pi / 2 + 2 * math.pi * center_turn
        lx, ly = x + math.cos(angle) * 18, y + math.sin(angle) * 18
        anchor_text = "start" if math.cos(angle) > 0.25 else "end" if math.cos(angle) < -0.25 else "middle"
        source_text = html.escape(str(row.sources).replace("|", " · "))
        zone_marks.append(
            f'<path d="{path}" class="zone {kind}"><title>{row.kind} {fmt_zone(row)} · {source_text}</title></path>'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.5" class="zone-dot {kind}"/>'
            f'<text x="{lx:.2f}" y="{ly + 4:.2f}" text-anchor="{anchor_text}" class="zone-label">{row.kind} {row.level:.0f}</text>'
        )

    current_turn = turns(latest_close)
    current_x, current_y = point(current_turn, max_turn)
    current_angle = -math.pi / 2 + 2 * math.pi * current_turn
    current_lx, current_ly = current_x + math.cos(current_angle) * 24, current_y + math.sin(current_angle) * 24
    current_anchor = "start" if math.cos(current_angle) > 0 else "end"

    supports = levels.loc[levels["kind"] == "支撑"].sort_values("distance", ascending=False)
    resistances = levels.loc[levels["kind"] == "压力"].sort_values("distance")
    nearest_support = supports.iloc[0]
    nearest_resistance = resistances.iloc[0]
    strongest = levels.sort_values(["source_count", "distance"], ascending=[False, True]).iloc[0]

    division = stats.loc[
        (stats["dimension"] == "space")
        & (stats["tool"] == "division")
        & (stats["direction"] == "both")
        & (stats["tolerance"].sub(0.025).abs() < 1e-9)
    ]
    clusters = stats.loc[
        (stats["dimension"] == "space")
        & (stats["tool"] == "clusters_2plus")
        & (stats["direction"] == "both")
        & (stats["tolerance"].sub(0.025).abs() < 1e-9)
    ]
    division_text = "无可用统计"
    if not division.empty:
        row = division.iloc[0]
        division_text = f"分割位命中 {row.hit_rate:.1%}，基线 {row.baseline:.1%}，超额 {row.excess:+.1%}，校正p={row.p_adjusted:.3f}"
    cluster_text = "无可用统计"
    if not clusters.empty:
        row = clusters.iloc[0]
        cluster_text = f"多源簇命中 {row.hit_rate:.1%}，基线 {row.baseline:.1%}，超额 {row.excess:+.1%}，校正p={row.p_adjusted:.3f}"

    wave_markdown = ""
    wave_section = ""
    if args.wave_report:
        wave_markdown = args.wave_report.read_text(encoding="utf-8").strip()
        if not wave_markdown:
            raise ValueError("--wave-report must not be empty")
        wave_section = (
            '<section class="wave-report" aria-label="波浪理论与未来情景">'
            + render_markdown(wave_markdown)
            + "</section>"
        )
    report_name = "江恩空间与波浪情景" if wave_markdown else "江恩空间共振"

    table_rows = []
    for row in levels.itertuples(index=False):
        table_rows.append(
            f"<tr><td>{row.kind}</td><td>{row.zone_lower:.2f}-{row.zone_upper:.2f}</td>"
            f"<td>{row.level:.2f}</td><td>{row.source_count}</td><td>{html.escape(str(row.sources).replace('|', ' · '))}</td></tr>"
        )

    document = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(args.symbol)}{report_name}</title>
<style>
:root{{--ink:#172033;--muted:#667085;--line:#d8dee9;--support:#2487e8;--resistance:#ef7a35;--square:#39a96b;--paper:#ffffff;--soft:#f6f8fb}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif}}
.page{{max-width:1240px;margin:0 auto;padding:24px}}h1{{margin:0;font-size:25px}}.sub{{margin-top:6px;color:var(--muted);font-size:13px}}
.layout{{display:grid;grid-template-columns:minmax(540px,1.25fr) minmax(340px,.75fr);gap:24px;margin-top:20px;align-items:start}}
.chart{{border:1px solid var(--line);padding:12px}}svg{{display:block;width:100%;height:auto}}.ring{{fill:none;stroke:var(--line);stroke-width:.8}}.spoke{{stroke:var(--line);stroke-width:.7;opacity:.7}}.spoke.major{{stroke-width:1.2;opacity:1}}.degree{{font-size:11px;fill:var(--muted)}}.spiral{{fill:none;stroke:var(--muted);stroke-width:1;opacity:.6}}.square-mark{{fill:var(--square);opacity:.72}}.zone{{fill:none;stroke-width:9;stroke-linecap:round;opacity:.83}}.zone.support{{stroke:var(--support)}}.zone.resistance{{stroke:var(--resistance)}}.zone-dot.support{{fill:var(--support)}}.zone-dot.resistance{{fill:var(--resistance)}}.zone-dot{{stroke:var(--paper);stroke-width:1.5}}.zone-label{{font-size:11px;fill:var(--ink);font-weight:600}}.current-ring{{fill:var(--paper);stroke:var(--ink);stroke-width:2}}.current-dot{{fill:var(--ink)}}.current-label{{font-size:12px;fill:var(--ink);font-weight:700}}.anchor{{fill:var(--ink)}}.anchor-label{{font-size:11px;fill:var(--muted)}}
.narrative{{border-top:3px solid var(--ink);padding-top:14px}}h2{{font-size:17px;margin:0 0 10px}}h3{{font-size:14px;margin:18px 0 7px}}p,li{{font-size:14px;line-height:1.65}}ul{{padding-left:19px;margin:7px 0}}.callout{{padding:11px 13px;background:var(--soft);border-left:3px solid var(--support)}}
table{{width:100%;border-collapse:collapse;margin-top:20px;font-size:12px}}th,td{{padding:8px 7px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:var(--soft)}}.disclaimer{{margin-top:18px;color:var(--muted);font-size:12px}}
.wave-report{{margin-top:28px;padding-top:20px;border-top:4px solid var(--ink)}}.wave-report h1{{font-size:22px;margin:0 0 14px}}.wave-report h2{{font-size:18px;margin:24px 0 10px}}.wave-report h3{{font-size:15px;margin:18px 0 8px}}.wave-report table{{font-size:12px;margin:12px 0 20px}}.wave-report blockquote{{margin:12px 0;padding:10px 14px;background:var(--soft);border-left:3px solid var(--resistance)}}.wave-report code{{font-size:12px}}.markdown-fallback{{white-space:pre-wrap;line-height:1.55}}
@media(max-width:900px){{.layout{{grid-template-columns:1fr}}.page{{padding:14px}}}}@media print{{.page{{max-width:none}}}}
</style>
</head>
<body><main class="page">
<h1>{html.escape(args.symbol)}{report_name}</h1>
<div class="sub">数据截至 {html.escape(as_of)} · 最新收盘 {latest_close:.2f} · Square-of-9锚点 {anchor:.2f}（{anchor_date}）</div>
<div class="layout">
<section class="chart" aria-label="江恩圆周图"><svg viewBox="0 0 700 700" role="img" aria-label="江恩价格螺旋与支撑压力共振区">
{''.join(rings)}{''.join(spokes)}<path d="{spiral}" class="spiral"/>{''.join(square_marks)}{''.join(zone_marks)}
<circle cx="{current_x:.2f}" cy="{current_y:.2f}" r="10" class="current-ring"/><circle cx="{current_x:.2f}" cy="{current_y:.2f}" r="3.7" class="current-dot"/>
<text x="{current_lx:.2f}" y="{current_ly + 4:.2f}" text-anchor="{current_anchor}" class="current-label">当前 {latest_close:.2f}</text>
<circle cx="350" cy="350" r="6" class="anchor"/><text x="350" y="372" text-anchor="middle" class="anchor-label">锚点 {anchor:.2f}</text>
</svg></section>
<section class="narrative">
<h2>文字结论</h2>
<p class="callout">当前价格位于最近支撑与压力之间。几何共振用于标出观察区，是否有效必须以历史超额和触碰后的匹配基线为准。</p>
<h3>当前结构</h3><ul>
<li>最近支撑：{fmt_zone(nearest_support)}</li>
<li>最近压力：{fmt_zone(nearest_resistance)}</li>
<li>来源最多：{strongest['kind']} {fmt_zone(strongest)}，{int(strongest['source_count'])}个独立来源</li>
</ul>
<h3>统计证据</h3><ul><li>{division_text}</li><li>{cluster_text}</li></ul>
<h3>使用边界</h3><p>优先解释八分法、三分位和扩展位；角度线用于辅助；圆周图和历史记忆用于定位。不得因线条密集或命中率高而忽略价格轴覆盖率，也不得把几何共振直接写成交易信号。</p>
</section></div>
<table><thead><tr><th>性质</th><th>成员区间</th><th>中心</th><th>独立来源数</th><th>来源</th></tr></thead><tbody>{''.join(table_rows)}</tbody></table>
{wave_section}
<div class="disclaimer">本报告为交易方法论的统计验证研究，不构成任何证券买卖建议，不预示未来表现。</div>
</main></body></html>"""
    (output_dir / "gann_circle.html").write_text(document, encoding="utf-8")
    if wave_markdown:
        (output_dir / "gann_wave_report.html").write_text(document, encoding="utf-8")

    markdown = f"""# {args.symbol}江恩空间共振结论

> 数据截至 {as_of}，最新收盘 {latest_close:.2f}；Square-of-9锚点为 {anchor:.2f}（{anchor_date}）。

## 当前结构

- 最近支撑：{fmt_zone(nearest_support)}。
- 最近压力：{fmt_zone(nearest_resistance)}。
- 来源最多：{strongest['kind']} {fmt_zone(strongest)}，{int(strongest['source_count'])}个独立来源。

## 统计证据

- {division_text}。
- {cluster_text}。

## 解释

优先使用八分法、三分位和扩展位；角度线只作辅助；圆周图与历史顶底、整数关口负责定位。几何共振必须和随机覆盖率、样本量及触碰后的匹配基线同时解释，不得直接写成交易信号。

本报告为交易方法论的统计验证研究，不构成任何证券买卖建议。
"""
    if wave_markdown:
        markdown += "\n---\n\n" + wave_markdown + "\n"
    (output_dir / "gann_summary.md").write_text(markdown, encoding="utf-8")
    print(output_dir / "gann_circle.html")
    if wave_markdown:
        print(output_dir / "gann_wave_report.html")
    print(output_dir / "gann_summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
