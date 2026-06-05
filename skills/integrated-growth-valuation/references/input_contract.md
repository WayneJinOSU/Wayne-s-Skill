# Input Contract

本文件定义投研、Financial Modeling、PEG 和 DCF 产物进入估值聚合层的接口。核心目标是避免上游因子越级变成新的聚合层估值结论。

## Required Handoffs

### dcf_financial_model_handoff

用途：把投研变量翻译成 `$financial-modeling` 可消费的三表/FCF 建模驱动，并保留后续 PEG-ready 与 DCF-ready 数据包所需候选字段。它不是 PEG-ready 数据包，也不是 DCF-ready 数据包，更不是估值报告。

必须覆盖 6 张表：

| 表 | 字段 |
| --- | --- |
| 历史锚表 | 年份、收入、毛利率、EBIT、扣非利润/经营利润、OCF、Capex、UFCF、来源 |
| 分业务驱动表 | 业务、收入、增速、ASP/价值量、出货/产量、毛利率、证据等级、来源、验证指标 |
| 费用与折旧表 | 年份、费用率、D&A、Capex、在建工程、转固节奏、爬坡损耗、来源 |
| 营运资本表 | 年份、DSO、DIO、DPO、应收、存货、合同负债、ΔNWC、现金流含义 |
| 情景表 | 情景、收入/利润/UFCF 关键假设、触发条件、降级条件、证据等级、可进入模型位置 |
| 数据缺口表 | 缺什么、影响哪个模型、是否可估算、等待什么数据、临时处理方式 |

驱动项表：

| 驱动项 | 业务来源 | 历史锚/来源 | 保守 | 中性 | 乐观 | 证据等级 | 财报验证指标 | 降级路径 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

DCF-ready UFCF 桥：

```text
EBIT*(1-Tax) + D&A - Capex - ΔNWC = UFCF
```

缺失项写“待 financial-modeling 补数/待财报补充”，不得硬编精确数字。

PEG-ready 候选字段也应在本 handoff 或 Financial Modeling 输入阶段保留：

```text
扣非利润/经营利润、2026E-2028E 中性与乐观候选锚、YoY、2-3 年 CAGR、
一致预期对照、股价/市值/股本、非经常性/少数股东/投资收益、OCF/UFCF 质量说明
```

这些字段必须由 `$financial-modeling` 统一口径后，才能形成正式 `<标的>_peg_ready_package.md`。

### peg_valuation_handoff

用途：声明 PEG/动态 PE 的估值路径、核心因子、情景准入、年份切换、质量折价和证伪规则。

它必须轻量，不能替代三表模型、PEG-ready 利润数据包或估值报告；它不进入 Financial Modeling。

必须包含：

```text
PEG 估值路径
核心估值因子接口
情景准入与年份切换规则
质量折价与证伪规则
```

核心因子接口：

| 因子 | 投研判断与证据等级 | 估值影响 | 情景准入 | 禁止用法 | 验证指标 |
| --- | --- | --- | --- | --- | --- |

模型输入契约：

| 下游模块 | 必须等待的字段 | 来源 | 缺失时处理 |
| --- | --- | --- | --- |
| Financial Modeling | 分业务收入/毛利率、扣非利润、EBIT、D&A、Capex、ΔNWC、OCF/UFCF、净债务/股本、股价/市值/股本、一致预期对照 | `dcf_financial_model_handoff` + 公告/一致预期/市场数据 | 列缺口，不自填 |
| PEG | `growth-stock-valuation` 输入包：扣非利润/经营利润、利润 YoY、2-3 年 CAGR、质量折价因子、证据等级、年份切换条件、当前市值/股价/股本/来源 | `$financial-modeling` 输出的 PEG-ready 数据包 + `peg_valuation_handoff` + 市场参数 | 无 PEG-ready 数据包时不调用正式 PEG |
| DCF | `dcf-model` 输入包：Revenue、EBIT、Tax、D&A、Capex、ΔNWC、UFCF、WACC 参数、终值、现金/债务/股本/现价、source comments | Financial Modeling 输出的 DCF-ready 数据包 + 市场参数 | 无 UFCF 或关键来源缺失时只做现金流质量提示，不调用正式 DCF |

## Evidence Admission

| 证据等级 | 可进入基准预测 | 可进入乐观情景 | 可进入敏感性/跟踪 | 说明 |
| --- | --- | --- | --- | --- |
| A | 是 | 是 | 是 | 公告、财报、监管、结构化数据 |
| B | 有条件 | 是 | 是 | IR、客户/竞品公告、认证、公开订单 |
| C | 否，除非多源交叉且有历史锚 | 有条件 | 是 | 券商、行业报告、份额估计、市场假设 |
| D | 否 | 否，除非明确标为趋势上沿 | 是 | 未交叉验证线索、交易热词、弱口径 |

## Minimal Company Context

若从聊天中直接启动，没有完整投研目录，也至少需要：

```text
company
business_segments
growth_drivers
evidence_grade
financial_model_drivers
valuation_adjustment_factors
tracking_indicators
latest_market_cap_price_date_source
```

缺少任一关键字段时，应把正式估值降级为“估值准备清单”。
