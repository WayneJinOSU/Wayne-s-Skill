# CHANGELOG

记录所有策略参数 / 配置 / 操作的变更。任何改动必须追加一行。

---

## 2026-05-30 — 策略包创建

- 锁定策略 `TRD_K20_ADV50M_NoKCB`
- 资金 5 万元(总盘 20 万的 25%)
- 调仓频率:季度(2026-06-01 起)
- 数据源:`/home/mira/files/experiments_archive/Y_l2_etf_mapping_20260529/kline_cache_all/`
- 证据:Z(+127.6%)、Z3(纯熊年 TRD 仍胜)、capsweep(5w 残值 96.3%)
- 文件:`README.md`, `quarterly_picks.py`, `current_holdings.json`(待生成)

## 2026-05-30 — 首批清单生成

- 跑 `quarterly_picks.py --cutoff 2026-05-29 --commit`
- 169 池 → 20 名单,实买 48,128 / 余 1,872 / 利用率 96.3%
- 写入 `current_holdings.json`(假设周一全额成交,实盘后需修正)

## 2026-05-31 — 执行脚本可靠性修正

- `HOME` 改为默认当前脚本目录,支持 `L2_ETF_LIVE_HOME` 覆盖
- `DATA_ROOT` 支持 `L2_ETF_DATA_ROOT` 覆盖
- 默认 cutoff 改为全池 K 线最新日期的众数,避免单只 ETF 先更新导致误判
- `--refresh-data` 改为显式报错,因为本包未包含行情刷新实现
- `--show-pool-size` 生效
- 调仓 SELL 单补全 ETF 名称和参考价
- README 修正首批 picks 文件名和数据刷新说明

## 2026-06-10 — 首次 ETF 建仓完成

- 用户确认 ETF 建仓全部完成
- 券商截图显示基金市值 49,210.60,浮盈 71.84
- `current_holdings.json` 状态更新为 `initial_build_completed_20_etfs`
- 注意:159381 当前股数高于原始等权目标,不做日内修正,留到下一次季度再平衡处理

## (TEMPLATE — 调仓日填写)

## YYYY-MM-DD — Qx 调仓

- cutoff = YYYY-MM-DD,capital = X
- 名单变动:进 X 只 / 出 X 只
- 实际成交价 vs 参考价偏离:平均 ±X.X%
- 备注:[停牌/分红/特殊事件]
