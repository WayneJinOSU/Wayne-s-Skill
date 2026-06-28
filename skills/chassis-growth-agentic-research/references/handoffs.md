# Handoffs And Financial Bridge

本文件承接 `SKILL.md` 的接力产物细则。主控必须在 Step 4 读取本文件，用于写入利润桥、跟踪体系、证据边界中的三表建模候选字段、PEG 因子、证据等级和缺口。`dcf_financial_model_handoff` 与 `peg_valuation_handoff` 只能在 `final_report` 完成、`skeptic_review` 存在、`final_report_gate.py` PASS 且 publication hygiene gate 以 `--fail-on medium` PASS 后生成。所有接力文件都不得写目标价、目标市值、买卖建议或最终估值结论。

Token discipline:

- handoff 只传递模型必要字段、证据等级、Fact-ID 和缺口，不复制完整中间研究稿。
- 已在 `<标的>_facts_core.md` 中存在的财务、分业务、产能、现金流和行情事实，只引用 Fact-ID。
- 不把 Gemini/媒体/券商长段写入 handoff；只保留已核验事实或 Lead-ID。
- 若某字段缺失，写“缺口/待补 + 等待来源”，不要用多个数据源堆砌近似值。

## Profit Bridge

利润桥研究写入 `<标的简称或代码>_profit_bridge.md`：

- 旧业务底盘利润、行业扩容中公司可获取份额、第二曲线新增利润、平台复用收益、扩张成本的方向性拆解。
- 默认输出轻量利润中枢：方向性区间、关键变量和敏感性；正式 PEG 交给 `$growth-stock-valuation`，正式 DCF 交给 `$dcf-valuation-workflow`。
- 保守、中性、乐观三种情景可以简化为“利润斜率情景”：分别由哪些市场变量触发，并说明证据强度。
- 必须处理并表利润、权益法收益、少数股东损益、非经常性损益和现金流质量，避免重复计算。
- 利润桥必须能解释变量如何影响收入、毛利率、费用率、折旧/财务费用/爬坡损耗、现金流和归母利润；不能只给三情景结论表。字段可按业务适用性裁剪；缺数据时写方向性区间、敏感性、缺口和验证指标，不硬凑完整预测表。

## Tracking Dashboard

跟踪体系写入 `<标的简称或代码>_tracking_dashboard.md`：

- 后续 2-4 个季度看什么：订单、收入、毛利率、现金流、应收存货、扩产进度、客户导入、产品放量、价格/成本/效率曲线、渗透率、份额和证据等级升级。
- 红黄绿灯：哪些指标说明逻辑增强，哪些说明只是旧业务修复或概念映射，哪些说明主线证伪。
- 对利润桥最敏感的 3-5 个变量和跟踪频率。

## Evidence Grading

证据边界与验证路径写入 `<标的简称或代码>_evidence_grading.md`，在终稿前、反方审查前后均可执行，但不得前置成删变量机制，也不要求终稿单独成章：

- A 级：公告、财报、交易所问询/回复、监管文件、结构化财务和行情数据。可作为事实底盘。
- B 级：公司 IR、官网、业绩说明会、客户/竞品公告、招投标、认证、产品发布、公开订单或量产线索。可作为经营验证。
- C 级：券商深度报告、行业报告、份额估计、TAM/SAM/SOM、公开专家观点。作为市场假设、情景变量和利润弹性来源。
- D 级：未交叉验证的产业链调研、专家访谈、未披露订单线索、交易热词、弱口径。作为跟踪触发器和待验证变量；若被公告、客户/竞品公开信息、券商/行业报告或多源口径交叉验证，可升为 C/B。
- 对每个核心变量说明：当前等级、为什么不能写成事实、为什么仍应保留、成立时利润传导、不成立时降级路径和验证指标。

## Post-Report Valuation Handoffs

Post-report handoffs are required research-to-valuation judgment interfaces:

```text
<prefix>_dcf_financial_model_handoff.md
<prefix>_peg_valuation_handoff.md
```

Generate both files only after:

```text
<prefix>_final_report.md exists
<prefix>_skeptic_review.md exists
scripts/final_report_gate.py returns PASS
publication_hygiene_gate.py --fail-on medium returns PASS
```

The handoff stage reads `final_report`, `skeptic_review`, `profit_bridge`, `tracking_dashboard`, `facts_core`, and only necessary supporting snippets.

The handoff files are not estimates, models, or data packages. They are mandatory outputs of the research workflow, carrying only research judgment for downstream valuation.

Use only these sections for `dcf_financial_model_handoff`:

| Section | Purpose |
| --- | --- |
| Status | Record `handoff_status: final_report_passed`, source paths, `final_report_gate_status`, `publication_hygiene_status`, generation time |
| Driver Admission | Map research variables to Base / Scenario / Sensitivity / Tracking-only |
| UFCF Guardrails | List forbidden substitutions, scenario-only variables, and downgrade triggers |
| Blocking Gaps | List gaps and whether they block Formal DCF |
| Prohibitions | No target price, no target market cap, no buy/sell language, no formal PEG or DCF conclusion |

`dcf_financial_model_handoff` must not output six modeling tables, rebuild historical statements, fill formal forecasts, or write WACC, terminal value, target price, target market cap, buy/sell language, or DCF conclusions.

Required sections for `peg_valuation_handoff`:

| Section | Purpose |
| --- | --- |
| Status | Record `handoff_status: final_report_passed`, source paths, `final_report_gate_status`, `publication_hygiene_status`, generation time |
| Research Verdict | Compress the final report's investment logic and key disconfirming conditions |
| PEG Factor Treatment | Map final-report factors to explicit PEG coefficient impact, scenario admission, year-switching limits, and validation metrics |
| Profit Anchor Discipline | List profit metric discipline, quality discounts, year discipline, scenario admission, and missing fields |
| Prohibitions | No target price, no target market cap, no buy/sell language, no formal PEG or DCF conclusion |

PEG Factor Treatment must include a coefficient-mechanics table:

| 因子 | 终稿判断 | 证据等级 | 对 PEG 系数的影响 | 机制说明 | 情景准入 | 年份切换影响 | 验证指标 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 收入兑现 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 利润质量 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 订单可见度 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 第二曲线 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 平台复用 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 现金流 / OCF |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| Capex / 产能 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 治理 / 信披 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 市场环境 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |

The "对 PEG 系数的影响" column must be specific enough for `$growth-stock-valuation` to choose a coefficient range. Examples: "caps neutral PEG at 1.1-1.2x", "allows optimistic PEG above neutral only after order amount is disclosed", "blocks 2028E year switching", "supports moving from 1.0x to 1.1x but not to 1.3x". Vague labels such as "positive", "negative", or "关注" are insufficient.

`Profit Anchor Discipline` only records profit metric discipline, quality discounts, scenario admission, year-switching conditions, and blocking gaps. It must not become an annual profit forecast table or fill missing valuation data for the downstream skill.

Formal valuation remains downstream: PEG is handled by `$growth-stock-valuation`; DCF is handled by `$dcf-valuation-workflow`. Valuation feedback may inform later tracking work, but must not rewrite research facts or flow back into `final_report` as target price, target market cap, buy/sell language, or a formal valuation conclusion.
