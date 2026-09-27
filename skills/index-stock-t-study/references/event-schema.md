# 事件和字段模式

以下字段名是推荐模式，不要求所有数据源原样提供，但导出报告应能映射到这些概念。

## 1. 因子定义表 `factor_levels`

| 字段 | 含义 |
|---|---|
| `factor_name` | `gann_resonance`、`fibonacci_38_2`、`golden_61_8`、`ma120`等 |
| `direction` | `resistance`或`support` |
| `level` | 价格位或带中心 |
| `band_low` / `band_high` | 候选区间；单点也应填同值 |
| `source_family` | 江恩分割、角度线、圆周图、斐波那契、均线等 |
| `anchor_start_date` / `anchor_end_date` | 计算波段或锚点日期 |
| `anchor_start_price` / `anchor_end_price` | 计算波段或锚点价格 |
| `confirm_date` | 该位可被研究者知道的最晚日期 |
| `calculated_at` | 生成因子位的时间 |
| `tolerance_pct` / `tolerance_points` | 冻结的事件容差 |
| `notes` | 缺口、方向、是否与其他因子同源 |

## 2. 指数事件表 `index_touch_events`

| 字段 | 含义 |
|---|---|
| `event_id` | 唯一事件编号 |
| `trade_date` | 交易日 |
| `index_symbol` | 指数代码/名称 |
| `factor_name` | 对应因子 |
| `direction` | 压力或支撑 |
| `bar_start` / `bar_end` | 5分钟K线起止时间 |
| `event_type` | `first_touch`、`cross`、`gap_above`、`gap_below`等 |
| `level` | 触碰时使用的价格位 |
| `bar_open` / `bar_high` / `bar_low` / `bar_close` | 事件K线OHLC |
| `distance_at_touch_pct` | 触碰/越过相对位的距离 |
| `signal_available_at` | 默认 `bar_end` |
| `dedup_group` | 同日同因子去重组 |
| `data_quality` | 完整、缺失、午休边界、异常等 |

## 3. 个股响应表 `stock_event_responses`

| 字段 | 含义 |
|---|---|
| `event_id` | 关联指数事件 |
| `stock_symbol` | 个股代码/名称 |
| `next_bar_start` | 事件后第一根完整个股5分钟K线 |
| `next_open` | 默认可执行参考价 |
| `next_high` / `next_low` / `next_close` | 第一根响应K线 |
| `future_5m_low` | 未来约5分钟最低价 |
| `future_15m_low` | 未来约15分钟最低价 |
| `future_30m_low` | 未来约30分钟最低价 |
| `post_touch_day_low` | 触碰后至收盘最低价 |
| `post_touch_day_low_time` | 当日最低出现时间 |
| `post_touch_day_close` | 当日收盘价 |
| `post_touch_day_low_vs_next_open_pct` | 日内最低相对参考价变化 |
| `post_touch_day_close_vs_next_open_pct` | 收盘相对参考价变化 |
| `post_touch_low_to_close_rebound_pct` | 最低价到收盘的修复幅度 |
| `future_5m_low_vs_next_open_pct` 等 | 各窗口低点相对参考价变化 |
| `window_status` | 完整、午休、停牌、涨跌停、缺失等 |

## 4. 对照表 `matched_controls`

| 字段 | 含义 |
|---|---|
| `control_id` | 唯一对照编号 |
| `stock_symbol` | 个股 |
| `trade_date` | 非事件交易日 |
| `bar_start` | 与事件匹配的5分钟钟点 |
| `match_rule` | 同钟点、同方向、波动率分层等 |
| `control_open` | 对照参考价 |
| `control_5m_low` / `control_15m_low` / `control_30m_low` | 对照窗口低点 |
| `control_day_low` / `control_day_close` | 对照剩余日最低/收盘 |
| `exclusion_reason` | 若排除，记录原因 |

## 5. 最低质量检查

- 同一 `event_id` 不应重复连接到同一股票的多根 `next_bar`；
- `next_bar_start` 必须晚于 `signal_available_at`；
- 事件窗口不得跨到下一交易日；
- 价格变化百分比的分母必须明确，默认是 `next_open`；
- 前复权个股与不复权个股不能在同一统计表混用；
- 若指数和个股5分钟时间戳时区或边界不同，必须先统一并记录偏差；
- 逐事件明细的均值应能复算汇总表，不能只保存四舍五入后的结果。
