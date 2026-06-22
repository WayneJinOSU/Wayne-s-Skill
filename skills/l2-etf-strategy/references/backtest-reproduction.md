# L2 ETF Backtest — 回测复现包

复现 `L2_ETF_LIVE/README.md` 中标注的 **TRD_K20_ADV50M 5w +120.8% / MDD -20.6% / Calmar 5.86** 这组绩效数字。

## 0. 准备数据

把 `L2_ETF_DATA_2026-05-29.zip` 解压到本目录的 `data/` 下,得到:

```
./
  run_capital_sweep.py    ← 主回测脚本(本次复现绩效的入口)
  run_z_full_etf.py       ← Z 期主线实验(参考)
  run_z_50k_capital_sweep.py
  run_z3_2023_only.py     ← 纯熊年验证
  hs300_daily.csv         ← regime 判定用(本次 TRD_K20_ADV50M 不依赖,但脚本启动会读)
  capsweep_summary.csv    ← 期望产出(用于 byte-diff 验证)
  summary_z_full_etf.txt  ← Z 期文字结论
  summary_z3_2023_only.txt
  data/
    all_etf_pool.csv      ← 623 只权益 ETF
    kline_cache_all/      ← 623 个日线 JSON
```

## 1. 一键复现

```bash
python3 run_capital_sweep.py
```

期望输出(stdout 最后一段):

```
TRD_K20_ADV50M  ret: 1w:+110.5%  2w:+117.8%  3w:+119.0%  5w:+120.8%  10w:+122.6%  20w:+123.3%
```

产物 `./baselines_capsweep/capsweep_summary.csv` 应与本目录下的 `capsweep_summary.csv` **byte-identical**:

```bash
diff ./baselines_capsweep/capsweep_summary.csv ./capsweep_summary.csv && echo OK
```

## 2. 关键参数(已在脚本顶部锁定)

| 项 | 值 | 说明 |
|---|---|---|
| 回测区间 | `2024-01-31 → 2026-05-26` | 27 个月,覆盖 2024 牛 / 2025 平 / 2026Q1 修复 |
| 调仓节点 | 每季度末(`2024-01-31` 起共 9 次) | 实盘版改成每季度月末最后一个交易日 |
| 资金扫描 | `[1w, 2w, 3w, 5w, 10w, 20w]` | 看 capital scaling |
| 信号 | `TRD = 120d 动量 Top K` / `REV = Bottom K` / `ADAPT = regime 切换` | regime 用 HS300 60日均线方向 |
| K | `[10, 20, 30]` | 持仓数 |
| ADV 门槛 | `[5e6, 20e6, 50e6]` (日均额下限,元) | 流动性过滤 |
| 手续费 | 单边 0.1% | |
| 手数 | 100 股/手 | |

## 3. README 里那组数字的对应行

`capsweep_summary.csv` 第 107 行:

```
TRD_K20_ADV50M,50000,110415.30190000003,120.83060380000008,-20.617516118591535,5.86058005750959,...
```

字段顺序:`strategy, capital, final, tot_ret, mdd, calmar, avg_cash_pct, avg_zero_alloc, avg_held, fee`

→ 5万资金,终值 11.04万,**总收益 +120.83%,MDD -20.62%,Calmar 5.86**。

## 4. 与实盘策略 `L2_ETF_LIVE/quarterly_picks.py` 的差异

| 项 | 回测 (`run_capital_sweep.py`) | 实盘 (`quarterly_picks.py`) |
|---|---|---|
| 池子 | 623 只(全 ETF) | 623 → 剔科创板 588/589 → 169 只 |
| 选股 | 单纯 Top K | 同 |
| 调仓 | 历史 9 个季度回放 | 单次 cutoff 出当期清单 |
| 输出 | NAV 曲线 + 统计 | picks_*.csv + trades_*.csv |

> 实盘的 `NoKCB`(剔科创板)只去掉了 0~2 只候选,对 TRD_K20_ADV50M 的入选名单基本无影响(科创板 588/589 在 ADV50M 门槛下能进 Top20 的极少)。如果想精确比对带 NoKCB 的回测,把 `run_capital_sweep.py` 中 `signal_topk()` 加一行 `if c.startswith(('588','589')): continue` 即可。

## 5. 其他实验脚本

- `run_z_full_etf.py` — Z 期主线,只跑 200K 单一资金量(用作 capsweep 的基准)
- `run_z_50k_capital_sweep.py` — 50K 单点验证(早期手工跑的版本)
- `run_z3_2023_only.py` — 纯 2023 熊年,验证 TRD 在熊市仍胜 REV/ADAPT

这三个不是复现 `+120.8%` 所必须,放进来供 Codex 交叉验证。
