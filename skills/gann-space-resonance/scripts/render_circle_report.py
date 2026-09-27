#!/usr/bin/env python3
"""Render a readable, self-contained Gann circle report.

The Square-of-9 price calculation remains unchanged. A bounded visual scale
keeps low-priced ETFs from collapsing into one tiny arc; exact prices stay in
tooltips and the table.
"""
from __future__ import annotations

import argparse
import html
import math
from pathlib import Path

import pandas as pd

SVG_SIZE = 900
CX = CY = SVG_SIZE / 2
OUTER = 390
INNER = 26


def _fmt(value: float, decimals: int) -> str:
    return f"{float(value):.{decimals}f}"


def point(turn: float, max_turn: float):
    radius = INNER + (OUTER - INNER) * turn / max(max_turn, 1e-9)
    angle = -math.pi / 2 + 2 * math.pi * turn
    return CX + math.cos(angle) * radius, CY + math.sin(angle) * radius


def spiral_path(start: float, end: float, max_turn: float, steps: int = 120) -> str:
    parts = []
    for index in range(steps + 1):
        turn = start + (end - start) * index / steps
        x, y = point(turn, max_turn)
        parts.append(("M" if index == 0 else "L") + f"{x:.2f},{y:.2f}")
    return "".join(parts)


def fmt_zone(row, decimals: int) -> str:
    return f"{_fmt(row.zone_lower, decimals)}-{_fmt(row.zone_upper, decimals)}（中心 {_fmt(row.level, decimals)}）"


def render_markdown(markdown_text: str) -> str:
    try:
        import mistune

        return mistune.create_markdown(plugins=["table"])(markdown_text)
    except ImportError:
        try:
            from markdown_it import MarkdownIt

            return MarkdownIt("commonmark", {"html": False}).enable("table").render(markdown_text)
        except ImportError:
            return f'<pre class="markdown-fallback">{html.escape(markdown_text)}</pre>'


def _label_position(x: float, y: float, angle: float, slot: int):
    tangent = (-math.sin(angle), math.cos(angle))
    offsets = (-58, -30, 0, 30, 58, -82, 82, -106, 106)
    tangential = offsets[slot % len(offsets)]
    radial = 30 + (slot % 3) * 12
    return (
        x + math.cos(angle) * radial + tangent[0] * tangential,
        y + math.sin(angle) * radial + tangent[1] * tangential,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the Gann circle and written interpretation")
    parser.add_argument("--results", type=Path, required=True, help="Directory created by run_index_study.py")
    parser.add_argument("--symbol", default="上证指数")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--wave-report", type=Path, default=None)
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
    decimals = 3 if max(abs(float(levels["zone_upper"].max())), abs(latest_close), abs(anchor)) < 10 else 2
    anchor_root = math.sqrt(anchor)

    def raw_turn(price: float) -> float:
        return (math.sqrt(max(float(price), 1e-12)) - anchor_root) / 2.0

    max_price = max(float(levels["zone_upper"].max()) * 1.06, latest_close * 1.10)
    raw_max = max(raw_turn(max_price), 1e-9)
    visual_scale = min(24.0, max(1.0, 5.5 / raw_max))

    def turns(price: float) -> float:
        return max(0.0, raw_turn(price) * visual_scale)

    max_turn = max(turns(max_price), 1.0)
    rings = "".join(
        f'<circle cx="{CX:.1f}" cy="{CY:.1f}" r="{INNER + (OUTER-INNER)*i/max_turn:.1f}" class="ring"/>'
        for i in range(1, math.floor(max_turn) + 1)
    )
    spokes = []
    for degree in range(0, 360, 45):
        angle = -math.pi / 2 + math.radians(degree)
        x2, y2 = CX + math.cos(angle) * OUTER, CY + math.sin(angle) * OUTER
        lx, ly = CX + math.cos(angle) * (OUTER + 28), CY + math.sin(angle) * (OUTER + 28)
        major = " major" if degree % 90 == 0 else ""
        spokes.append(
            f'<line x1="{CX:.1f}" y1="{CY:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="spoke{major}"/>'
            f'<text x="{lx:.1f}" y="{ly+6:.1f}" text-anchor="middle" class="degree">{degree}°</text>'
        )
    spiral = spiral_path(0, max_turn, max_turn, 1000)
    square_marks = []
    for i in range(math.floor(max_turn / 0.25) + 1):
        display_turn = i * 0.25
        actual_turn = display_turn / visual_scale
        price = (anchor_root + 2 * actual_turn) ** 2
        x, y = point(display_turn, max_turn)
        square_marks.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" class="square-mark"><title>{_fmt(price, decimals)} · {(display_turn%1)*360:.0f}°</title></circle>'
        )

    zone_marks = []
    placed_labels = []
    for kind_name, group in (("支撑", levels[levels.kind == "支撑"]), ("压力", levels[levels.kind == "压力"])):
        # Keep the chart readable when a broad index produces many levels.
        # All zones remain drawn and listed in the table; only the four
        # nearest levels per side receive text labels on the circle.
        label_indices = set(group.loc[group["distance"].abs().sort_values().index].head(4).index)
        label_slot_counter = 0
        for row in group.sort_values("level").itertuples(index=True):
            kind = "support" if kind_name == "支撑" else "resistance"
            start, end = turns(row.zone_lower), turns(row.zone_upper)
            center_turn = turns(row.level)
            x, y = point(center_turn, max_turn)
            angle = -math.pi / 2 + 2 * math.pi * center_turn
            source_text = html.escape(str(row.sources).replace("|", " · "))
            mark = f'<path d="{spiral_path(start,end,max_turn,70)}" class="zone {kind}"><title>{kind_name} {fmt_zone(row, decimals)} · {source_text}</title></path><circle cx="{x:.1f}" cy="{y:.1f}" r="8" class="zone-dot {kind}"/>'
            if row.Index in label_indices:
                # Start resistance labels at a different tangential slot so
                # nearby support and resistance zones do not share a baseline.
                label_slot = label_slot_counter + (2 if kind_name == "压力" else 0)
                label_slot_counter += 1
                lx, ly = _label_position(x, y, angle, label_slot)
                anchor_text = "start" if lx >= CX else "end"
                label = f"{kind_name} {_fmt(row.level, decimals)}"
                # Resolve approximate text-box collisions while preserving the
                # leader line to the actual zone point. This is display-only.
                width = max(58.0, len(label) * 10.0)
                # Keep long index labels inside the SVG viewport.
                if anchor_text == "end" and lx - width < 24:
                    lx = width + 24
                elif anchor_text == "start" and lx + width > SVG_SIZE - 24:
                    lx = SVG_SIZE - width - 24
                for _ in range(8):
                    left = lx if anchor_text == "start" else lx - width
                    right = lx + width if anchor_text == "start" else lx
                    conflict = False
                    for prev_left, prev_right, prev_y in placed_labels:
                        if right >= prev_left - 8 and left <= prev_right + 8 and abs(ly - prev_y) < 26:
                            ly += 30 if ly >= prev_y else -30
                            conflict = True
                            break
                    if not conflict:
                        break
                ly = min(SVG_SIZE - 20, max(20, ly))
                placed_labels.append((left, right, ly))
                mark += f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{lx:.1f}" y2="{ly-5:.1f}" class="leader {kind}"/><text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor_text}" class="zone-label">{label}</text>'
            zone_marks.append(mark)

    current_turn = turns(latest_close)
    current_x, current_y = point(current_turn, max_turn)
    current_angle = -math.pi / 2 + 2 * math.pi * current_turn
    # Keep the latest-price label away from the nearest pressure/support label.
    # A dedicated outer slot is more legible when an ETF current price sits beside a nearby level.
    current_lx, current_ly = _label_position(current_x, current_y, current_angle, 8)
    current_anchor = "start" if current_lx >= CX else "end"
    supports = levels.loc[levels.kind == "支撑"].sort_values("distance", ascending=False)
    resistances = levels.loc[levels.kind == "压力"].sort_values("distance")
    nearest_support, nearest_resistance = supports.iloc[0], resistances.iloc[0]
    strongest = levels.sort_values(["source_count", "distance"], ascending=[False, True]).iloc[0]

    def stat_text(tool: str) -> str:
        rows = stats.loc[(stats.dimension == "space") & (stats.tool == tool) & (stats.direction == "both") & (stats.tolerance.sub(0.025).abs() < 1e-9)]
        if rows.empty:
            return "无可用统计"
        row = rows.iloc[0]
        name = "分割位" if tool == "division" else "多源簇"
        return f"{name}命中 {row.hit_rate:.1%}，基线 {row.baseline:.1%}，超额 {row.excess:+.1%}，校正p={row.p_adjusted:.3f}"

    wave_markdown = args.wave_report.read_text(encoding="utf-8").strip() if args.wave_report else ""
    wave_section = '<section class="wave-report" aria-label="波浪理论与未来情景">' + render_markdown(wave_markdown) + "</section>" if wave_markdown else ""
    report_name = "江恩空间与波浪情景" if wave_markdown else "江恩空间共振"
    table_rows = "".join(
        f'<tr><td>{row.kind}</td><td>{_fmt(row.zone_lower, decimals)}-{_fmt(row.zone_upper, decimals)}</td><td>{_fmt(row.level, decimals)}</td><td>{row.source_count}</td><td>{html.escape(str(row.sources).replace("|", " · "))}</td></tr>'
        for row in levels.itertuples(index=False)
    )
    legend = (
        f'<g class="legend" transform="translate(34 34)" aria-label="图例">'
        f'<rect x="0" y="0" width="204" height="116" rx="10" class="legend-box"/>'
        f'<line x1="16" y1="25" x2="48" y2="25" class="legend-line support"/>'
        f'<text x="60" y="31" class="legend-text">支撑区间</text>'
        f'<line x1="16" y1="55" x2="48" y2="55" class="legend-line resistance"/>'
        f'<text x="60" y="61" class="legend-text">压力区间</text>'
        f'<circle cx="32" cy="85" r="6" class="legend-current"/>'
        f'<text x="60" y="91" class="legend-text">当前收盘</text>'
        f'</g>'
    )
    svg = f'''<svg viewBox="0 0 {SVG_SIZE} {SVG_SIZE}" role="img" aria-label="{html.escape(args.symbol)}江恩价格螺旋与支撑压力共振区">{rings}{''.join(spokes)}<path d="{spiral}" class="spiral"/>{''.join(square_marks)}{''.join(zone_marks)}<circle cx="{current_x:.1f}" cy="{current_y:.1f}" r="15" class="current-ring"/><circle cx="{current_x:.1f}" cy="{current_y:.1f}" r="5" class="current-dot"/><text x="{current_lx:.1f}" y="{current_ly+6:.1f}" text-anchor="{current_anchor}" class="current-label">当前 {_fmt(latest_close, decimals)}</text><circle cx="{CX:.1f}" cy="{CY:.1f}" r="9" class="anchor"/><text x="{CX:.1f}" y="{CY+34:.1f}" text-anchor="middle" class="anchor-label">锚点 {_fmt(anchor, decimals)}</text>{legend}</svg>'''
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(args.symbol)}{report_name}</title><style>
:root{{--ink:#172033;--muted:#667085;--line:#d8dee9;--support:#2788e8;--resistance:#ef7a35;--square:#49ad78;--paper:#fff;--soft:#f6f8fb}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif}}.page{{max-width:1500px;margin:0 auto;padding:26px 30px 32px}}h1{{margin:0;font-size:28px}}.sub{{margin-top:6px;color:var(--muted);font-size:14px}}.layout{{display:grid;grid-template-columns:minmax(660px,1.18fr) minmax(360px,.82fr);gap:24px;margin-top:18px;align-items:start}}.chart{{border:1px solid var(--line);padding:12px;background:#fff}}svg{{display:block;width:100%;height:auto}}.ring{{fill:none;stroke:var(--line);stroke-width:1}}.spoke{{stroke:var(--line);stroke-width:.9;opacity:.72}}.spoke.major{{stroke-width:1.5;opacity:.95}}.degree{{font-size:15px;fill:var(--muted)}}.spiral{{fill:none;stroke:#9aa8ba;stroke-width:1.2;opacity:.65}}.square-mark{{fill:var(--square);opacity:.78}}.zone{{fill:none;stroke-width:12;stroke-linecap:round;opacity:.88}}.zone.support{{stroke:var(--support)}}.zone.resistance{{stroke:var(--resistance)}}.zone-dot.support{{fill:var(--support)}}.zone-dot.resistance{{fill:var(--resistance)}}.zone-dot{{stroke:#fff;stroke-width:2.5}}.leader{{stroke-width:1.4;opacity:.78}}.leader.support{{stroke:var(--support)}}.leader.resistance{{stroke:var(--resistance)}}.zone-label{{font-size:18px;fill:var(--ink);font-weight:750;paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round}}.current-ring{{fill:#fff;stroke:var(--ink);stroke-width:3}}.current-dot{{fill:var(--ink)}}.current-label{{font-size:20px;fill:var(--ink);font-weight:800;paint-order:stroke;stroke:#fff;stroke-width:6px}}.anchor{{fill:var(--ink)}}.anchor-label{{font-size:16px;fill:var(--muted);paint-order:stroke;stroke:#fff;stroke-width:5px}}.legend-box{{fill:#fff;fill-opacity:.94;stroke:var(--line);stroke-width:1}}.legend-line{{stroke-width:8;stroke-linecap:round}}.legend-line.support{{stroke:var(--support)}}.legend-line.resistance{{stroke:var(--resistance)}}.legend-current{{fill:var(--ink);stroke:#fff;stroke-width:2}}.legend-text{{font-size:15px;fill:var(--ink);font-weight:650}}.narrative{{border-top:3px solid var(--ink);padding-top:13px}}h2{{font-size:17px;margin:0 0 10px}}h3{{font-size:14px;margin:17px 0 7px}}p,li{{font-size:14px;line-height:1.65}}ul{{padding-left:19px;margin:7px 0}}.callout{{padding:11px 13px;background:var(--soft);border-left:3px solid var(--support)}}table{{width:100%;border-collapse:collapse;margin-top:18px;font-size:12px}}th,td{{padding:8px 7px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:var(--soft)}}.disclaimer{{margin-top:16px;color:var(--muted);font-size:12px}}.wave-report{{margin-top:28px;padding-top:20px;border-top:4px solid var(--ink)}}.wave-report h1{{font-size:22px;margin:0 0 14px}}.wave-report h2{{font-size:18px;margin:24px 0 10px}}.wave-report table{{font-size:12px;margin:12px 0 20px}}.wave-report blockquote{{margin:12px 0;padding:10px 14px;background:var(--soft);border-left:3px solid var(--resistance)}}.markdown-fallback{{white-space:pre-wrap;line-height:1.55}}@media(max-width:950px){{.layout{{grid-template-columns:1fr}}.page{{padding:14px}}.zone-label{{font-size:15px}}.degree{{font-size:13px}}}}@media print{{.page{{max-width:none}}}}</style></head><body><main class="page"><h1>{html.escape(args.symbol)}{report_name}</h1><div class="sub">数据截至 {html.escape(as_of)} · 最新收盘 {_fmt(latest_close, decimals)} · Square-of-9锚点 {_fmt(anchor, decimals)}（{anchor_date}）</div><div class="layout"><section class="chart" aria-label="江恩圆周图">{svg}</section><section class="narrative"><h2>文字结论</h2><p class="callout">当前价格位于最近支撑与压力之间。圆周几何用于标出观察区，是否有效仍需结合历史超额与触碰后的匹配基线。</p><h3>当前结构</h3><ul><li>最近支撑：{fmt_zone(nearest_support, decimals)}</li><li>最近压力：{fmt_zone(nearest_resistance, decimals)}</li><li>来源最多：{strongest['kind']} {fmt_zone(strongest, decimals)}，{int(strongest['source_count'])} 个独立来源</li></ul><h3>统计证据</h3><ul><li>{stat_text('division')}</li><li>{stat_text('clusters_2plus')}</li></ul><h3>使用边界</h3><p>优先解释八分法、三分位和扩展位；角度线用于辅助；圆周图和历史记忆用于定位。图上螺旋做了显示尺度归一化，实际价位仍使用原始公式计算。</p></section></div><table><thead><tr><th>性质</th><th>成员区间</th><th>中心</th><th>独立来源数</th><th>来源</th></tr></thead><tbody>{table_rows}</tbody></table>{wave_section}<div class="disclaimer">本报告为交易方法论的统计验证研究，不构成任何证券买卖建议，不预示未来表现。</div></main></body></html>'''
    (output_dir / "gann_circle.html").write_text(document, encoding="utf-8")
    if wave_markdown:
        (output_dir / "gann_wave_report.html").write_text(document, encoding="utf-8")
    summary = f"# {args.symbol}江恩空间共振结论\n\n> 数据截至 {as_of}，最新收盘 {_fmt(latest_close, decimals)}；Square-of-9锚点为 {_fmt(anchor, decimals)}（{anchor_date}）。\n\n## 当前结构\n\n- 最近支撑：{fmt_zone(nearest_support, decimals)}。\n- 最近压力：{fmt_zone(nearest_resistance, decimals)}。\n- 来源最多：{strongest['kind']} {fmt_zone(strongest, decimals)}，{int(strongest['source_count'])}个独立来源。\n\n## 统计证据\n\n- {stat_text('division')}。\n- {stat_text('clusters_2plus')}。\n\n## 解释\n\n优先使用八分法、三分位和扩展位；角度线只作辅助；圆周图与历史顶底、整数关口负责定位。圆周螺旋为显示尺度归一化，价位计算仍按原始 Square-of-9 公式。\n\n本报告为交易方法论的统计验证研究，不构成任何证券买卖建议。\n"
    if wave_markdown:
        summary += "\n---\n\n" + wave_markdown + "\n"
    (output_dir / "gann_summary.md").write_text(summary, encoding="utf-8")
    print(output_dir / "gann_circle.html")
    if wave_markdown:
        print(output_dir / "gann_wave_report.html")
    print(output_dir / "gann_summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
