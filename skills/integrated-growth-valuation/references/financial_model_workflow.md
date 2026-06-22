# Financial Model Workflow

Financial Modeling 是共同预测底稿，不是最终估值模型。

## Required Forecast Years

默认覆盖：

```text
2026E
2027E
2028E
```

若当前年份变化，使用最近 3 个完整预测年，并说明年份切换原因。

## Output Table

至少输出：

| 年份 | 收入 | 毛利率 | 费用率 | EBIT | 扣非利润 | D&A | Capex | ΔNWC | OCF | UFCF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |

情景分为：

```text
底线/中性/乐观
```

正式 PEG/DCF 模型默认使用中性和乐观；底线主要用于风险和证伪，不堆成第三套目标价。

## Required Handoff Tables

`dcf_financial_model_handoff` 优先按 6 张表读取：

| 表 | 进入 Financial Modeling 后的用途 |
| --- | --- |
| 历史锚表 | 校准历史收入、利润率、EBIT、扣非利润、OCF、Capex 和 UFCF |
| 分业务驱动表 | 建收入拆分、产品结构、ASP/价值量、出货/产量和毛利率假设 |
| 费用与折旧表 | 建费用率、D&A、Capex、在建工程、转固节奏和爬坡损耗 |
| 营运资本表 | 建 DSO/DIO/DPO、应收、存货、合同负债和 ΔNWC |
| 情景表 | 区分底线/中性/乐观，决定哪些变量进入 Base、Bull 或 Sensitivity |
| 数据缺口表 | 标记无法硬算的字段，并决定是否暂停 PEG-ready 或 DCF-ready 输出 |

Financial Modeling 基于这些表输出两包数据：

```text
PEG-ready：扣非利润/经营利润、YoY、CAGR、一致预期对照、股本/市值、质量说明
DCF-ready：Revenue、EBIT、Tax、D&A、Capex、ΔNWC、UFCF、现金/债务/股本、WACC、终值输入和 assumption ledger
```

## Bridge Logic

必须把投研变量翻译到财务科目：

| 投研变量 | 财务映射 |
| --- | --- |
| 第二曲线放量 | 分业务收入、产品结构、毛利率 |
| 平台复用 | 费用率、毛利率、复购、研发摊薄 |
| 扩产 | Capex、D&A、产能利用率、爬坡损耗 |
| 客户认证/订单 | 收入可见度、合同负债、应收、存货 |
| 原材料/良率 | 毛利率、库存跌价、现金流 |
| 治理/信披风险 | 折价、暂停条件、历史锚可信度 |

## UFCF Discipline

DCF 只能消费 UFCF：

```text
UFCF = EBIT * (1 - Tax Rate) + D&A - Capex - ΔNWC
```

若 Capex、D&A 或 ΔNWC 缺少事实口径，不得用净利润替代 DCF。Formal DCF 应停止；Scenario DCF 可用带来源类型、置信度、区间和敏感性的业务推理/proxy 继续建模；Reverse DCF 可反推当前市值隐含现金流。

## DCF Model Handoff Package

Financial Modeling 完成共同预测底稿后，应额外整理给 `/Users/a/.codex/skills/dcf-model` 的输入包：

| 字段 | 要求 |
| --- | --- |
| 历史与预测期 | 至少 1 个历史基准年 + 5-7 个显性预测年；成长股可延长至现金流进入稳态 |
| 经营预测 | Revenue、Revenue growth、EBIT margin、EBIT、Tax rate、NOPAT |
| UFCF 桥 | Formal DCF 不得缺 D&A、Capex、ΔNWC、UFCF；Scenario DCF 可用区间/proxy，但必须进 assumption ledger |
| 情景 | Bear/Base/Bull；弱证据变量不得进入 Base |
| WACC 输入 | Risk-free rate、ERP、Beta、pre-tax cost of debt、tax rate、E/(D+E)、D/(D+E)；若为推理区间，标注 source type 和 confidence |
| 终值 | Terminal growth 或 exit multiple；必须说明来源和稳态约束 |
| Equity bridge | Cash、Debt、minority interest/other claims、shares、current price/market cap |
| 来源 | 每个硬编码输入给出 source comment，可追溯到财报、公告、市场数据或明确假设 |

Financial Modeling 不输出最终目标市值；DCF 计算、Excel 模型、敏感性和 validation 由 `dcf-model` 完成。

## Quality Checks

- 扣非利润与归母利润差异大时，PEG 使用扣非利润或经营利润。
- 并表、少数股东、权益法收益必须拆清，避免重复计算。
- Capex 高增但折旧未同步变化时，必须说明转固节奏。
- 存货/应收快于收入时，DCF 情景必须体现现金流压力。
- OCF/净利长期偏低时，PEG 需质量折价，DCF 需解释 UFCF 弱的原因。
