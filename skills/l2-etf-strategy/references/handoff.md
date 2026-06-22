# L2 ETF Strategy / Experiment Handoff

生成日: 2026-06-10

这个包只整理 ETF 季度策略线,不包含 Turtle 个股实盘脚本,也不包含后续 VCP 个股策略实验。

## 1. 当前策略结论

最终实盘策略为 `TRD_K20_ADV50M_NoKCB`:

- 资金段: 50,000 RMB
- 池子: 东方财富全 A ETF/LOF 清洗后的权益 ETF 池
- 实盘候选: 剔除科创板 ETF 代码前缀 `588` / `589`
- 流动性过滤: 过去 60 日均成交额 >= 50,000,000 RMB
- 信号: 120 日动量 Top 20
- 权重: 20 只等权,每只约 2,500 RMB
- 调仓频率: 季度
- 止盈止损: 无,季度中原则上不动
- Regime/REV/ADAPT: 不启用。此前实验显示 ETF 池里 TRD only 优于 REV/ADAPT。

实盘状态更新:

- 2026-06-10 用户确认首次 ETF 建仓全部完成
- 券商截图显示基金市值 49,210.60,浮盈 71.84
- `01_live_strategy/L2_ETF_LIVE/current_holdings.json` 已更新为 `initial_build_completed_20_etfs`
- 当前唯一偏差: `159381` 股数高于原始等权目标,留到下一次季度再平衡处理

核心回测数字:

- 2024-01 到 2026-05: 5 万资金版本总收益约 +120.8%,最大回撤约 -20.6%,Calmar 约 5.86
- 2023 单一熊年验证: TRD 在 2023 仍明显跑赢 MARKET 与 REV/ADAPT,因此没有采用反转/自适应切换

## 2. 包内目录

```text
01_live_strategy/
  L2_ETF_LIVE/
    README.md                  # 实盘策略身份卡和 SOP
    quarterly_picks.py          # 实盘生成季度 picks/trades 的主脚本
    current_holdings.json       # 当前实盘 ETF 持仓记录
    picks_*.csv                 # 调仓目标清单
    trades_*.csv                # 建仓/调仓下单清单
    nav_log.csv                 # 净值记录

02_backtest_reproduction/
  L2_ETF_BACKTEST/
    README.md                   # 回测复现说明
    run_capital_sweep.py         # 复现 +120.8% 的主入口
    run_z_full_etf.py            # 2024-2026 ETF 全市场实验
    run_z3_2023_only.py          # 2023 熊年验证
    capsweep_summary.csv         # 期望结果
    data/all_etf_pool.csv        # ETF 池
    data/kline_cache_all/*.json  # ETF 日线缓存

03_source_data/
  L2_ETF_DATA_2026-05-29/
    all_etf_pool.csv
    kline_cache_all/*.json

04_repro_output/
  L2_ETF_REPRO_OUT_2026-05-31/
    picks_2026-05-29.csv
    trades_2026-05-29.csv

05_reference_results/
  summary_z_full_etf.txt
  summary_z3_2023_only.txt
  capsweep_summary.csv
```

## 3. 如何复现

依赖: Python 环境需要有 `pandas` / `numpy`。本机普通 `python3` 不带 pandas,已使用 Codex bundled Python 验证通过。

进入:

```bash
cd 02_backtest_reproduction/L2_ETF_BACKTEST
python3 run_capital_sweep.py
```

期望输出里应包含:

```text
TRD_K20_ADV50M  ret: 1w:+110.5%  2w:+117.8%  3w:+119.0%  5w:+120.8%  10w:+122.6%  20w:+123.3%
```

再核对:

```bash
diff ./baselines_capsweep/capsweep_summary.csv ./capsweep_summary.csv
```

无输出即一致。

本包生成前已完成一次验证:

- `run_capital_sweep.py` 运行成功
- 输出包含 `TRD_K20_ADV50M ... 5w:+120.8%`
- `baselines_capsweep/capsweep_summary.csv` 与 `capsweep_summary.csv` diff 一致

## 4. 如何跑实盘季度清单

进入:

```bash
cd 01_live_strategy/L2_ETF_LIVE
python3 quarterly_picks.py
```

输出:

- `picks_YYYY-MM-DD.csv`: 当期 Top20 目标 ETF
- `trades_YYYY-MM-DD.csv`: 相对 `current_holdings.json` 的买卖差额

注意:

- `quarterly_picks.py` 不自动刷新行情缓存。若要刷新数据,先更新 `kline_cache_all`,再运行脚本。
- 季度中不做新闻调仓,不做止盈止损。
- 若某 ETF 停牌/退市,在下次调仓时用候补顺延处理。

## 5. 数据来源说明

- ETF 池: 东方财富 MK0021 ETF/LOF 池,清洗掉货币、债券、LOF 等非权益标的。
- K 线: 腾讯 qfqday 日线缓存。
- 成交额估算: `volume * close * 100`,用于 60 日 ADV 过滤。
- HS300: 仅用于早期 regime/ADAPT 对照实验;当前实盘策略不启用 regime 切换。

## 6. 重要边界

- 本包是 ETF 策略线,不要用 Turtle 规则解释 ETF 的买卖。
- ETF 策略已独立于当前个股 Turtle/VCP 策略。
- ETF 实盘资金段按 50,000 RMB 设计;超出或低于这个资金段需要重新检查手数、现金利用率和分散度。
