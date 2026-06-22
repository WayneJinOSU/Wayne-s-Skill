# Handoffs And Financial Bridge

本文件承接 `SKILL.md` 的接力产物细则。主控必须在 Step 4 读取本文件，用于写入利润桥、跟踪体系、证据边界中的三表建模候选字段、PEG 因子、证据等级和缺口。正式 `dcf_financial_model_handoff` 与 `peg_valuation_handoff` 只能在 `final_report` 完成、`skeptic_review` 存在且 `final_report_gate.py` PASS 后生成。所有接力文件都不得写目标价、目标市值、买卖建议或最终估值结论。

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
- 利润桥必须能解释变量如何影响收入、毛利率、费用率、折旧/财务费用/爬坡损耗、现金流和归母利润；不能只给三情景结论表。

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

## DCF Financial Model Handoff

终稿通过后的三表建模接力输入写入 `<标的简称或代码>_dcf_financial_model_handoff.md`，用于后续 `$dcf-valuation-workflow` 调用 `$financial-modeling` 建三表/FCF/UFCF，并形成 DCF-ready 数据包；它不是 DCF-ready 数据包本身，也不是估值结论，不进入 `final_report`。Step 4 只在利润桥、跟踪体系和证据边界中准备这些字段的候选口径与缺口。

必须从旧业务底盘、第二曲线、行业空间份额、执行信号、利润桥、跟踪体系和证据分级中抽取可建模驱动，分清公司事实、市场口径和自有假设。

至少覆盖：

- 收入拆分/增速。
- 毛利率。
- 费用率。
- 折旧摊销。
- capex/revenue。
- DSO/DIO/DPO。
- 税率。
- 利息/债务。
- 少数股东/投资收益。
- 经营现金流和 FCF 质量。

必须输出驱动项表：

| 驱动项 | 业务来源 | 历史锚/来源 | 保守 | 中性 | 乐观 | 证据等级 | 财报验证指标 | 降级路径 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

必须输出 DCF-ready UFCF 桥所需字段：`EBIT*(1-Tax)+D&A-Capex-ΔNWC`。缺数据写“待 financial-modeling 补数/待财报补充”，不得硬编精确数字。若某变量只能支撑利润情景、不能支撑三表预测，必须标为“情景压力测试”，不得写成基准模型假设。

可为后续 PEG-ready 数据包保留候选利润字段：扣非利润或经营利润、2026E-2028E 中性与乐观候选锚、YoY、2-3 年 CAGR、一致预期对照、当前市值/股价/股本来源、非经常性/少数股东/投资收益和 OCF/UFCF 质量说明；正式 PEG-ready 口径以后续 `$growth-stock-valuation` 生成为准。

每张表应控制为模型消费所需的最小行数：历史锚、核心分业务、核心驱动和关键缺口即可。原始三表、完整公告列表、完整研报列表和宽表 CSV 不进入 handoff。

## PEG Valuation Handoff

终稿通过后的 PEG 估值接力输入写入 `<标的简称或代码>_peg_valuation_handoff.md`。它是“投研因子 -> `$growth-stock-valuation`”的接口协议，不是半份估值报告，也不是三表模型说明。正式利润锚、PEG-ready 数据包和估值口径由 `$growth-stock-valuation` 独立生成或确认；本文件只定义 PEG 因子、倍数边界、情景准入、年份切换、质量折价和 PEG 系数影响机制。Step 4 只在跟踪体系和证据边界中准备 PEG 因子的候选口径与缺口。

`peg_valuation_handoff` 不得做：

- 不输出目标价、目标市值、买卖建议、最终估值结论或“当前贵不贵”。
- 不替代 PEG-ready 利润数据包，不自行发明 2026E-2028E 精确利润、YoY 或 CAGR。
- 不把 TAM/SAM/SOM、客户线索、扩产、机器人/汽车/热管理等远期变量直接写成基准收入或利润。
- 不重复 `dcf_financial_model_handoff` 的三表建模假设；只列 PEG 必须等待的字段和缺口处理。

`peg_valuation_handoff` 必须包含：

### PEG 估值路径

用 3-6 句话说明：PEG/动态 PE 框架、主年份纪律、为什么适合当前公司阶段、哪些数据缺口会阻止正式 PEG。成长股通常先做 2027E 守门，再在强触发条件下讨论 2028E 年份切换。

### PEG 核心因子接口

| 因子 | 投研判断与证据等级 | 对 PEG/PE 的影响 | 情景准入 | 禁止用法 | 验证指标 |
| --- | --- | --- | --- | --- | --- |
| 旧业务底盘 |  | 影响利润下限和基础容忍度 | 基准/中性 | 不把周期峰值当永久利润 | 收入、毛利率、订单、现金流 |
| 第二曲线 |  | 影响收入增速、CAGR、PEG 上修空间 | 中性/乐观/敏感性 | 不把客户线索直接写成利润 | 客户、订单、收入、回款 |
| 平台复用 |  | 影响毛利率、费用率、成长质量 | 中性/乐观 | 不把“平台化”当无成本协同 | 毛利率、费用率、复购 |
| 利润质量 |  | 影响 PEG 折价/溢价 | 所有情景 | 不用归母替代扣非或经营利润 | 扣非、OCF、费用率 |
| 治理/信披风险 |  | 影响折价、暂停条件和历史锚可信度 | 所有情景 | 不忽略未落地监管风险 | 监管结论、审计意见 |

### PEG 候选利润锚骨架

下表只记录投研候选锚和情景边界，不是正式 PEG-ready 数据包。正式利润锚、YoY 和 CAGR 以后续 `$growth-stock-valuation` 的 PEG-ready 生成或确认结果为准；本 handoff 必须保留给 PEG skill 的利润锚边界和 PEG 系数机制。

| 年份 | 利润口径 | 一致预期 | 投研候选中性 | 投研候选乐观 | YoY 增速 | CAGR 区间 | 证据等级 | 备注 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 2025A | 归母/扣非/经营利润 |  |  |  |  |  | A |  |
| 2026E | 归母/扣非/经营利润 |  |  |  |  |  | A/B/C | 待 `$financial-modeling` 复核 |
| 2027E | 归母/扣非/经营利润 |  |  |  |  |  | A/B/C | PEG 主年份守门 |
| 2028E | 归母/扣非/经营利润 |  |  |  |  |  | C/D | 只作年份切换 |

## Valuation Follow-Up Boundary

后续正式估值分两条独立链路：

- PEG 侧交给 `$growth-stock-valuation`，反馈可用于订单/收入、毛利率、费用率、年份切换和一致预期上修跟踪。
- DCF 侧交给 `$dcf-valuation-workflow`，反馈可用于 Capex、D&A、Delta NWC、应收、存货、合同负债、OCF/UFCF 和现金转化率跟踪。

任何估值反馈不得改写前置研究事实，不得把目标价、目标市值或买卖建议倒灌进 `final_report`。

## Post-Report Valuation Handoff Override

This section overrides any earlier wording in this file when the two conflict.

The formal valuation handoff is a post-report pair:

```text
<prefix>_dcf_financial_model_handoff.md
<prefix>_peg_valuation_handoff.md
```

They must be generated only after:

```text
<prefix>_final_report.md exists
<prefix>_skeptic_review.md exists
scripts/final_report_gate.py returns PASS
```

The handoff stage should be run by one valuation-handoff subagent or equivalent post-report pass. It reads `final_report`, `skeptic_review`, `profit_bridge`, `tracking_dashboard`, `facts_core`, and only necessary supporting snippets.

The handoff pair is not an estimate and not a model. It is the execution bridge from completed research to later `$growth-stock-valuation` and `$dcf-valuation-workflow`.

Required sections for `dcf_financial_model_handoff`:

| Section | Purpose |
| --- | --- |
| Status | Record `handoff_status: final_report_passed`, source paths, gate status, generation time |
| Financial Modeling Inputs | List revenue, margin, expense, capex, D&A, working-capital, cash-flow quality, net debt/share-count fields and gaps |
| DCF-Ready Notes | Preserve UFCF bridge requirements and data gaps; do not produce DCF value |
| Prohibitions | No target price, no target market cap, no buy/sell language, no formal PEG or DCF conclusion |

Required sections for `peg_valuation_handoff`:

| Section | Purpose |
| --- | --- |
| Status | Record `handoff_status: final_report_passed`, source paths, gate status, generation time |
| Research Verdict | Compress the final report's investment logic and key disconfirming conditions |
| PEG Factor Treatment | Map final-report factors to explicit PEG coefficient impact, scenario admission, year-switching limits, and validation metrics |
| PEG-Ready Boundaries | List profit metric discipline, candidate anchors, quality discounts, year discipline, and missing fields |
| Prohibitions | No target price, no target market cap, no buy/sell language, no formal PEG or DCF conclusion |

If either handoff is missing or older than `final_report`, downstream modeling and valuation skills must stop before formal valuation and request the post-report handoff pair.

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
