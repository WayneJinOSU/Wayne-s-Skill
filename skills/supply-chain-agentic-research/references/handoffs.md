# Handoffs And Financial Bridge

本文件承接利润桥、跟踪体系、三表/FCF 建模候选输入和 PEG 估值候选输入。Handoff 是投研系统给后续估值的判断接口，不是正式估值结论；只能在 `final_report` 完成、`skeptic_review` 存在且 `final_report_gate.py` PASS 后生成。

Token discipline:

- handoff 只传递模型必要字段、证据等级、Fact-ID 和缺口，不复制完整中间研究稿。
- 已在 `<标的>_facts_core.md` 中存在的财务、分业务、产能、现金流和行情事实，只引用 Fact-ID。
- 不把 Gemini/媒体/券商长段写入 handoff；只保留已核验事实或 Lead-ID。
- 若某字段缺失，写“缺口/待补 + 等待来源”，不要用多个数据源堆砌近似值。

## Profit Bridge

`<标的>_profit_bridge.md` 是研究阶段的利润传导解释，不是正式预测表或三表模型。它必须把市场变量翻译成轻量、可裁剪、带证据等级的利润桥；能量化则给方向性区间或敏感性，不能量化则写缺口、待验证来源和验证指标，不得硬凑完整数字。

按业务适用性覆盖以下变量，不要求每家公司每一项都完整填数：

- 存量供应链利润底盘：历史高点、当前利润、分业务收入和毛利率、现金流质量。
- 新周期新增利润：订单/出货/排产、产品代际、ASP、份额、产能利用率和良率。
- 价格与利润传导：新旧产品价差、单机/单柜/单车/单套价值量、高端毛利率溢价、原材料转嫁率、良率和折旧扣减。
- 第二曲线和归母口径：控股/参股公司、权益法收益、少数股东损益、投资收益和并表边界。
- 敏感性：高端占比、ASP、毛利率、产能利用率、良率、原材料涨价留存率、少数股东损益和现金流转换率。

必须输出一张轻量利润桥表，字段可按业务裁剪：

| 模块/变量 | 利润传导机制 | 方向性区间/敏感性 | 关键假设或缺口 | 证据等级/Fact-ID | 跟踪验证 |
| --- | --- | --- | --- | --- | --- |

表格中的历史事实字段优先写 `Fact-ID + 数值摘要`，不要重复粘贴完整来源段落。

## Tracking Dashboard

`<标的>_tracking_dashboard.md` 必须把主线和利润桥转成未来 4-8 个季度的可跟踪信号：

- 绿色增强信号：哪些订单、认证、毛利率、现金流、产品占比、客户 capex 或竞品信号说明主线升级。
- 黄灯观察信号：哪些指标说明仍需等待，不足以升级也不足以证伪。
- 红色警报信号：哪些指标出现会使利润模型下修或主线降级。
- 每个信号必须给出阈值、方向或可观察口径。

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
```

The handoff stage reads `final_report`, `skeptic_review`, `profit_bridge`, `tracking_dashboard`, `facts_core`, and only necessary supporting snippets.

The handoff files are not estimates, models, or data packages. They are mandatory outputs of the research workflow, carrying only research judgment for downstream valuation.

Use only these sections for `dcf_financial_model_handoff`:

| Section | Purpose |
| --- | --- |
| Status | Record `handoff_status: final_report_passed`, source paths, gate status, generation time |
| Driver Admission | Map research variables to Base / Scenario / Sensitivity / Tracking-only |
| UFCF Guardrails | List forbidden substitutions, scenario-only variables, and downgrade triggers |
| Blocking Gaps | List gaps and whether they block Formal DCF |
| Prohibitions | No target price, no target market cap, no buy/sell language, no formal PEG or DCF conclusion |

`dcf_financial_model_handoff` must not output six modeling tables, rebuild historical statements, fill formal forecasts, or write WACC, terminal value, target price, target market cap, buy/sell language, or DCF conclusions.

Required sections for `peg_valuation_handoff`:

| Section | Purpose |
| --- | --- |
| Status | Record `handoff_status: final_report_passed`, source paths, gate status, generation time |
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
| 技术路线 / 价值量 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 原材料 / 成本 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 现金流 / OCF |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| Capex / 产能 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 治理 / 信披 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |
| 市场环境 |  |  | 抬高/压低/封顶/无影响 | 说明为什么影响 PEG 系数 |  |  |  |

The "对 PEG 系数的影响" column must be specific enough for `$growth-stock-valuation` to choose a coefficient range. Examples: "caps neutral PEG at 1.1-1.2x", "allows optimistic PEG above neutral only after order amount is disclosed", "blocks 2028E year switching", "supports moving from 1.0x to 1.1x but not to 1.3x". Vague labels such as "positive", "negative", or "关注" are insufficient.

`Profit Anchor Discipline` only records profit metric discipline, quality discounts, scenario admission, year-switching conditions, and blocking gaps. It must not become an annual profit forecast table or fill missing valuation data for the downstream skill.

Formal valuation remains downstream: PEG is handled by `$growth-stock-valuation`; DCF is handled by `$dcf-valuation-workflow`. Valuation feedback may inform later tracking work, but must not rewrite research facts or flow back into `final_report` as target price, target market cap, buy/sell language, or a formal valuation conclusion.
