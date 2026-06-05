# PEG Engine Handoff

PEG / 动态 PE 是成长定价模型，独立回答市场按成长股逻辑愿意给多少倍数。`integrated-growth-valuation` 不自行计算 PEG；正式聚合前必须已经存在 `$growth-stock-valuation` 输出的动态 PEG、复合 PEG、一致预期差、隐含利润、年份切换和目标市值区间。

## Inputs

必须来自 Financial Modeling 和 `peg_valuation_handoff`，交给 `$growth-stock-valuation` 使用：

```text
扣非利润或经营利润
利润 YoY
2-3 年利润 CAGR
质量折价因子
证据等级
年份切换条件
当前市值、股价、股本、日期和来源
```

不能使用：

- 非经常性损益作为核心利润。
- 无财务底稿支持的远期利润。
- C/D 级弱线索直接支撑基准 PEG。

## Required growth-stock-valuation Outputs

正式 PEG 产物由 `$growth-stock-valuation` 输出到研究目录。聚合模式使用专用文件名，避免覆盖聚合 scorecard：

```text
<标的>_peg_valuation_deepdive.md
<标的>_peg_valuation_scorecard.md
```

最低内容：

| 模块 | 必须展示的内容 |
| --- | --- |
| 市场锚 | 当前市值、股价、股本、TTM/Forward PE、数据日期和来源 |
| 一致预期 | 2026E/2027E/2028E 利润、EPS、机构数、预期变化方向 |
| 自有利润桥 | 中性/乐观利润锚，与一致预期差异 |
| 动态 PEG | 利润锚、净利润增速、PEG、对应 PE、目标市值、触发条件 |
| 复合 PEG | PE 分母、CAGR 区间、复合增速、复合 PEG、对应 PE、目标市值 |
| 当前隐含 | 当前市值隐含利润/PE/PEG、市场已交易到哪一步 |
| 年份纪律 | 2027E 守门；是否允许切换到 2028E；必要触发条件 |
| 风险约束 | 质量折价、证伪点、下修触发、不能进入基准的弱证据 |

## Aggregator Consumption

聚合层只读取 `<标的>_peg_valuation_deepdive.md` 和 `<标的>_peg_valuation_scorecard.md` 的关键结果：

| 情景 | 利润锚 | PEG/PE | 目标市值 | 当前隐含 | 触发条件 | 证伪点 |
| --- | ---: | ---: | ---: | --- | --- | --- |

不要在 aggregation report 中重算 PEG，只引用 `$growth-stock-valuation` 输出并提示它与 DCF 的差异来源。

## Year Discipline

若当前日期在 2026 年：

- PEG 主年份默认先做 `2027E` 守门。
- 不得直接把 `2028E` 写成中性目标市值锚。
- `2028E` 只能作为估值年份切换或乐观上沿，并绑定触发条件。

触发条件可以是：

```text
订单/客户验证
利润上修
毛利率和费用率同步兑现
OCF/UFCF 改善
板块处于结构牛或产业主升浪
```

## PEG Band Guidance

PEG 档位判断由 `$growth-stock-valuation` 完成。聚合层只能摘录其结论：

| 状态 | PEG 容忍度 |
| --- | --- |
| 周期修复且利润质量一般 | 0.8-1.0x |
| 收入兑现但利润待确认 | 1.0-1.2x |
| 半兑现平台成长且订单/客户链较强 | 1.1-1.3x |
| 兑现型平台龙头且现金流和毛利率同步 | 1.2-1.4x |
| 产业主升浪稀缺龙头 | 1.3-1.5x |
| 高潮期或趋势上沿 | >1.5x，只能作为上沿，不能作为中枢 |

## Quality Discounts

必须折价或限制年份切换的情况：

- 扣非利润弱于归母利润。
- OCF/净利偏低，或 UFCF 连续为负。
- 存货、应收、合同资产快于收入。
- Capex 高且产能利用率未验证。
- 毛利率依赖市场口径而非财报验证。
- 治理、信披、监管或审计风险未消除。
