# DCF Engine Handoff

DCF 是现金流内在价值模型，与 PEG 平行独立。`integrated-growth-valuation` 不自行计算 DCF；正式聚合前必须已经存在 `/Users/a/.codex/skills/dcf-model` 输出的 Excel 模型、估值摘要、敏感性和校验结果。

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

没有 UFCF 时，不做正式 DCF。

## UFCF Formula

```text
UFCF = EBIT * (1 - Tax Rate) + D&A - Capex - ΔNWC
```

DCF 不得用净利润、归母利润、扣非利润或 EBITDA 直接替代 UFCF。

## Required dcf-model Outputs

正式 DCF 产物由 `skills/dcf-model` 输出到研究目录：

```text
<标的>_dcf_model.xlsx
<标的>_dcf_summary.md
<标的>_dcf_validation.json
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

`dcf_model.xlsx` 必须遵守 `skills/dcf-model` 的规则：所有推导单元格使用 Excel 公式；硬编码只允许 raw historical inputs、assumption drivers 和 market data；每个蓝色输入值必须带 source comment。

## Validation

交付前运行：

```bash
python3 /Users/a/.codex/skills/dcf-model/scripts/validate_dcf.py \
  research_artifacts/<标的>/<标的>_dcf_model.xlsx \
  research_artifacts/<标的>/<标的>_dcf_validation.json
```

`dcf_validation.json` 若出现 formula error、terminal growth >= WACC，或模型无法定位核心 DCF 表，不能称为正式 DCF 完成。

如采用退出倍数，必须解释退出倍数与长期增长、ROIC 和行业成熟度是否一致。

## Aggregator Consumption

聚合层只读取 `dcf_summary.md`、`dcf_validation.json` 和 workbook 的关键结果：

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

- 缺 UFCF。
- Capex 或 ΔNWC 缺失且无法合理估算。
- 终值贡献过高但没有稳态假设说明。
- 预测依赖 D 级弱线索。
