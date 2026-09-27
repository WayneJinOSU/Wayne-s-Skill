# 江恩多时钟时间研究

## 何时使用

当用户要求具体时间点、变盘日、时间之窗、波浪等时、C3/C4/C5结束时间，或复盘某个日期为何有效时，除空间研究外运行多时钟时间账本。时间研究仍不能单独定方向。

## 机械时钟

1. `major_natural`：5%因果ZigZag拐点的预设自然日周期；主容差±2自然日，±3日只作敏感性。
2. `major_trading`：5%拐点后的21、34、55、89、144个交易间隔。
3. `local_trading`：2.5%因果ZigZag拐点后的5、8、13、21、34个交易间隔。
4. `wave_duration`：审定段落的0.618、1、1.618倍时长，同时计算自然日与交易日。

前三类由脚本机械生成；第四类必须通过人工段落CSV声明，脚本不得根据比例反推浪型。

## 运行

只需要KhQuant指数库时：

```bash
python scripts/build_multiclock_time_ledger.py \
  --db /absolute/path/to/index.duckdb \
  --start 2021-01-01 --end 2026-08-31 \
  --projection-end 2026-11-30 \
  --output /absolute/path/to/output
```

如有交易所日历、宽度与波浪段落：

```bash
python scripts/build_multiclock_time_ledger.py \
  --daily /absolute/path/to/index_daily.csv \
  --future-sessions /absolute/path/to/trade_calendar.csv \
  --breadth /absolute/path/to/daily_breadth.csv \
  --peer-indices /absolute/path/to/peer_indices_long.csv \
  --wave-segments /absolute/path/to/wave_segments.csv \
  --projection-end 2026-11-30 \
  --output /absolute/path/to/output
```

`wave_segments.csv`字段：

```csv
scenario,segment,start_date,end_date,projection_anchor_date,projection_anchor_confirm_date
preferred,C3,2026-07-01,2026-07-20,2026-08-18,2026-08-19
```

`projection_anchor_confirm_date`为必填项，应写该投影起点在当时可被确认的日期。窗口早沿会裁剪到确认日之后。

宽度文件需要`date`或`trade_date`，以及`advance_ratio`；也可提供`up`和`traded`由脚本计算。建议同时保留`equal_weight_ret`、`down`。

宽基文件采用长表`date,symbol,close`，至少包含两个、建议包含沪深300、中证500、中证1000和创业板。脚本以日涨跌和MA5/MA20同步比例生成跨指数确认；它是确认证据，不是独立定浪规则。

## 输出

- `major_pivots_5pct.csv`：父级因果拐点。
- `local_pivots_2_5pct.csv`：低级别因果拐点。
- `multiclock_windows.csv`：所有时间窗口与来源族。
- `wave_duration_windows.csv`：可选的波浪等时投影。
- `multiclock_density.csv`：窗口数、锚点数和独立来源族数。
- `daily_confirmation_ledger.csv`：极值候选、价格反转、宽度反转、指数确认、扩散与跨指数确认。
- `multiclock_summary.md`：当前密集窗口和确认状态。

若未来日期未提供交易所日历，脚本用工作日估算并标记`estimated_weekday`。正式报告不得把该日期写成精确交易日，须在获取交易所日历后重跑。

## 解释纪律

- `window_count`表示成员数，`source_family_count`表示时钟种类；`independent_family_count`采用更保守的因果来源口径。
- 5%/2.5%、自然日/交易日时钟都来自价格拐点机制，统一归入`price_pivot_clock`；同一锚点的多个比例、同一族的多个周期、多个锚点或多个容差均不得重复加权。人工波浪等时归入`wave_duration`，但共享结构账本或事后选锚时仍须披露依赖关系。
- 低级别交易日窗口可以提示极值或首次确认，但不能越级确认父级浪。
- 区分`pivot_date`、`confirm_date`和窗口内实际出现的`extreme_date/confirmation_date`。
- 时间窗与价格支撑/压力、宽度和跨指数方向相冲突时，记录“时间到而方向未确认”。
- 对某个历史日期的解释必须先证明该窗口能够使用当时已经确认的锚点生成；事后新增锚点的漂亮解释一律剔除。

## 统计边界

自然日、交易日和波浪等时分别计算覆盖率、命中率和多重校正。增加时钟会提高日期覆盖率，因此不得用“更多窗口命中更多拐点”证明提升。正式提高模型权重前，至少滚动检验极值、首次确认和周线确认三类目标，并与简单的固定日期覆盖基线比较。
