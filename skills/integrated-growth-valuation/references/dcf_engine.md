# DCF Engine Handoff

DCF 是现金流内在价值模型，与 PEG 平行独立。`integrated-growth-valuation` 不自行计算 DCF；聚合前必须已经存在 `/Users/a/.codex/skills/dcf-model` 输出的 Formal、Scenario 或 Reverse DCF 结果。

## Inputs

必须来自 Financial Modeling 的 DCF-ready 数据包：

```text
Revenue
EBIT
Tax Rate
D&A
Capex
ΔNWC
UFCF
Cash
Debt
Minority interest / Other claims
Shares outstanding
Current share price / market cap
Risk-free rate
Equity risk premium
Beta
Pre-tax cost of debt
Capital structure weights
Terminal growth rate or exit multiple
Source comments for hardcoded inputs
```

没有 UFCF 时，不做 Formal DCF。若有可解释的推理区间、proxy 和置信度台账，可以做 Scenario DCF；若只有当前市值和少量边界，可以做 Reverse DCF。

## UFCF Formula

```text
UFCF = EBIT * (1 - Tax Rate) + D&A - Capex - ΔNWC
```

DCF 不得用净利润、归母利润、扣非利润或 EBITDA 直接替代 UFCF。

## Required dcf-model Outputs

Formal DCF 产物由 `skills/dcf-model` 输出到研究目录：

```text
<标的>_dcf_model.xlsx
<标的>_dcf_summary.md
<标的>_dcf_validation.json
```

Scenario DCF 产物：

```text
<标的>_dcf_assumption_ledger.md
<标的>_scenario_dcf_summary.md
<标的>_scenario_dcf_model.xlsx
<标的>_scenario_dcf_validation.json
```

其中 Excel 和 validation 在时间允许时优先生成；若只输出 Markdown 情景模型，必须在 summary 内完整展示公式、关键输入区间、情景结果和敏感性。

Reverse DCF 产物：

```text
<标的>_dcf_assumption_ledger.md
<标的>_reverse_dcf_summary.md
```

最低内容：

| 模块 | 必须展示的行 |
| --- | --- |
| Scenario blocks | Bear/Base/Bull assumptions, selected case, revenue growth, EBIT margin, D&A, Capex, ΔNWC |
| Operating forecast | Revenue、Revenue growth、EBIT margin、EBIT、Tax rate、NOPAT |
| UFCF bridge | D&A、Capex、Change in NWC、UFCF |
| Discounting | Discount factor、PV of UFCF、Terminal growth、Terminal value、PV of terminal value |
| EV bridge | PV of explicit UFCF、PV of terminal value、Enterprise value、Cash、Debt、Minority interest、Equity value、Shares、Value per share |
| WACC build-up | Risk-free rate、ERP、Beta、Cost of equity、Pre-tax cost of debt、Tax rate、After-tax cost of debt、E/(D+E)、D/(D+E)、WACC |
| Sensitivity | Odd-sized WACC × terminal growth sensitivity; center cell equals base case |
| Checks | UFCF tie-out, WACC weights, terminal spread, EV bridge, source completeness, formula-error validation |

Formal 或 Scenario Excel 模型必须遵守 `skills/dcf-model` 的规则：所有推导单元格使用 Excel 公式；硬编码只允许 raw historical inputs、assumption drivers 和 market data；每个蓝色输入值必须带 source comment。Scenario DCF 还必须包含 Assumption Ledger，标注 Fact / Consensus / Business Inference / Proxy / Reverse Implied、置信度和敏感性处理。

## Validation

交付前运行：

```bash
python3 /Users/a/.codex/skills/dcf-model/scripts/validate_dcf.py \
  research_artifacts/<标的>/<标的>_dcf_model.xlsx \
  research_artifacts/<标的>/<标的>_dcf_validation.json
```

Formal `dcf_validation.json` 若出现 formula error、terminal growth >= WACC，或模型无法定位核心 DCF 表，不能称为正式 DCF 完成。Scenario validation 若未通过，聚合层可读取 summary，但必须标注“Scenario DCF 未通过 Excel 校验”。

如采用退出倍数，必须解释退出倍数与长期增长、ROIC 和行业成熟度是否一致。

## Aggregator Consumption

聚合层只读取 DCF 输出的关键结果，不重算 DCF。Formal 读取 `dcf_summary.md`、`dcf_validation.json` 和 workbook 的关键结果；Scenario/Reverse 读取 summary 和 assumption ledger。

| 情景 | 显性期 UFCF | WACC | 终值假设 | 企业价值 | 净债务调整 | 股权价值 | 每股价值/目标市值 |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |

不要在 aggregation report 中重算 DCF，只引用 DCF 输出并提示它与 PEG 的差异来源。

## Growth Stock DCF Risks

成长股 DCF 常见失真：

- 显性期太短，导致大量价值来自终值。
- 远期毛利率和费用率过于乐观。
- Capex、D&A、营运资本与扩张节奏不匹配。
- 用高增长期利润率外推稳态。
- 忽略应收、存货和合同资产对 UFCF 的吞噬。

## Interpretation

DCF 不是 PEG 的校验工具，而是由 `skills/dcf-model` 独立输出的价值锚。

- DCF 显著低于 PEG：说明成长定价依赖未来兑现，现金流尚未支撑。
- DCF 接近 PEG：说明利润弹性和现金流质量收敛。
- DCF 高于 PEG：检查市场是否低估现金流、或公司是否进入低增长高现金回收期。

## Hard Stop Conditions

出现以下情况，只输出 DCF 准备清单：

- 缺 UFCF 且无法给出推理区间或 reverse-implied 路径。
- Capex 或 ΔNWC 缺失且无法合理估算或做敏感性。
- 终值贡献过高但没有稳态假设说明。
- 预测依赖 D 级弱线索。
- 非事实输入没有 source type、confidence、range 或 sensitivity treatment。
