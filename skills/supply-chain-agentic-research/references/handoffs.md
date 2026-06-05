# Handoffs And Financial Bridge

本文件承接利润桥、跟踪体系、三表/FCF 建模候选输入和 PEG 估值候选输入。正式 handoff 是后续模型消费接口，不是正式估值结论；只能在 `final_report` 完成、`skeptic_review` 存在且 `final_report_gate.py` PASS 后生成。

Token discipline:

- handoff 只传递模型必要字段、证据等级、Fact-ID 和缺口，不复制完整中间研究稿。
- 已在 `<标的>_facts_core.md` 中存在的财务、分业务、产能、现金流和行情事实，只引用 Fact-ID。
- 不把 Gemini/媒体/券商长段写入 handoff；只保留已核验事实或 Lead-ID。
- 若某字段缺失，写“缺口/待补 + 等待来源”，不要用多个数据源堆砌近似值。

## Profit Bridge

`<标的>_profit_bridge.md` 必须把市场变量翻译成可计算或半可计算的利润桥，至少覆盖：

- 存量供应链利润底盘：历史高点、当前利润、分业务收入和毛利率、现金流质量。
- 新周期新增利润：订单/出货/排产、产品代际、ASP、份额、产能利用率和良率。
- 价格与利润传导：新旧产品价差、单机/单柜/单车/单套价值量、高端毛利率溢价、原材料转嫁率、良率和折旧扣减。
- 第二曲线和归母口径：控股/参股公司、权益法收益、少数股东损益、投资收益和并表边界。
- 敏感性：高端占比、ASP、毛利率、产能利用率、良率、原材料涨价留存率、少数股东损益和现金流转换率。

必须输出表格：

| 模块 | 收入/出货/产量 | ASP/价值量 | 产品占比 | 毛利率 | 毛利 | 费用/折旧/良率扣减 | 投资收益/少数股东 | 归母贡献 | 来源等级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

表格中的历史事实字段优先写 `Fact-ID + 数值摘要`，不要重复粘贴完整来源段落。

## Tracking Dashboard

`<标的>_tracking_dashboard.md` 必须把主线和利润桥转成未来 4-8 个季度的可跟踪信号：

- 绿色增强信号：哪些订单、认证、毛利率、现金流、产品占比、客户 capex 或竞品信号说明主线升级。
- 黄灯观察信号：哪些指标说明仍需等待，不足以升级也不足以证伪。
- 红色警报信号：哪些指标出现会使利润模型下修或主线降级。
- 每个信号必须给出阈值、方向或可观察口径。

## DCF Financial Model Handoff

终稿通过后的 `<标的>_dcf_financial_model_handoff.md` 用于后续 `$financial-modeling` 建三表/FCF，并拆成 PEG-ready 与 DCF-ready 两个数据包；它不是 PEG-ready/DCF-ready 数据包本身，也不是估值结论，不进入 `final_report`。Step 4 只在利润桥、跟踪体系和证据边界中准备这些字段的候选口径与缺口。

必须按固定模板输出 6 张表，字段缺失时写“缺口/待补”，不得省略表格：

1. 历史锚表：`年份 | 收入 | 毛利率 | EBIT | 扣非利润/经营利润 | OCF | Capex | UFCF | 来源`
2. 分业务驱动表：`业务 | 收入 | 增速 | ASP/价值量 | 出货/产量 | 毛利率 | 证据等级 | 来源 | 验证指标`
3. 费用与折旧表：`年份 | 费用率 | D&A | Capex | 在建工程 | 转固节奏 | 爬坡损耗 | 来源`
4. 营运资本表：`年份 | DSO | DIO | DPO | 应收 | 存货 | 合同负债 | ΔNWC | 现金流含义`
5. 情景表：`情景 | 收入/利润/UFCF 关键假设 | 触发条件 | 降级条件 | 证据等级 | 可进入模型位置`
6. 数据缺口表：`缺什么 | 影响哪个模型 | 是否可估算 | 等待什么数据 | 临时处理方式`

必须输出驱动项表或把驱动项嵌入上述表格：

| 驱动项 | 供应链变量来源 | 历史锚/来源 | 底线 | 基准 | 上行 | 证据等级 | 财报验证指标 | 降级路径 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

必须输出 DCF-ready UFCF 桥所需字段：

```text
EBIT * (1 - Tax) + D&A - Capex - ΔNWC
```

缺数据写“待 financial-modeling 补数/待财报补充”，不得硬编精确数字。订单、排产、扩产、认证、ASP 和毛利率若仍是市场口径，只能进入情景或敏感性，不能伪装成基准模型事实。

每张表应控制为模型消费所需的最小行数：历史年度/季度锚、核心分业务、核心驱动和关键缺口即可。原始三表、完整公告列表、完整研报列表和宽表 CSV 不进入 handoff。

## PEG Valuation Handoff

终稿通过后的 `<标的>_peg_valuation_handoff.md` 只供 `$growth-stock-valuation` 判断 PEG/动态 PE 档位、年份切换、质量折价、PEG 系数影响机制和证伪边界；不得输出目标价、目标市值、买卖建议或最终估值结论。Step 4 只在跟踪体系和证据边界中准备 PEG 因子的候选口径与缺口。

必须覆盖：

- 当前股价、市值、PE/PB、日期和来源，只用于后续估值 skill，不进入 `final_report`。
- 当前阶段：预期型、半兑现型、兑现型、右侧重估型、高潮型或证伪型。
- 市场正在交易什么：利润上修、估值年份切换、SOTP 重估，还是情绪溢价；这些只写入 handoff，不进入 final_report 的正式结论。
- PEG 候选利润锚和情景边界：2025A/2026E/2027E/2028E 的一致预期、投研候选中性、投研候选乐观、YoY 增速、CAGR 区间、利润口径和证据等级。
- PEG 修正项：低基数、非经常性、并表/少数股东、现金流质量、订单前置、毛利率弹性、原材料价格和产能利用率如何影响 PEG 折价或溢价。
- 深度估值需要回答的 3-5 个问题。

PEG 候选利润锚骨架：

| 年份 | 利润口径 | 一致预期 | 投研候选中性 | 投研候选乐观 | YoY 增速 | CAGR 区间 | 证据等级 | 备注 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 2025A | 归母/扣非/经营利润 |  |  |  |  |  | A |  |
| 2026E | 归母/扣非/经营利润 |  |  |  |  |  | A/B/C |  |
| 2027E | 归母/扣非/经营利润 |  |  |  |  |  | A/B/C |  |
| 2028E | 归母/扣非/经营利润 |  |  |  |  |  | C/D |  |

PEG 核心因子接口：

| 因子 | 当前判断 | 对 PEG/PE 的影响 | 证据等级 | 估值处理 |
| --- | --- | --- | --- | --- |
| 主线类型 | 收入兑现/利润待确认/平台身份切换/第二曲线放量 | 决定基础 PEG 档位 |  |  |
| 兑现阶段 | 预期型/半兑现/兑现型/高潮型 | 决定乐观 PEG 能否给满 |  |  |
| 利润质量 | 扣非、现金流、毛利率、费用率是否匹配 | 影响 PEG 折价/溢价 |  |  |
| 订单可见度 | 合同负债、订单、客户认证、在手订单 | 决定 2027E 利润可信度 |  |  |
| 第二曲线 | 是否从题材进入订单/收入 | 决定是否允许年份切换 |  |  |
| 竞争壁垒 | 客户粘性、技术壁垒、份额提升 | 决定平台溢价 |  |  |
| 市场环境 | 震荡市/结构牛/主升浪/高潮期 | 决定倍数上限 |  |  |
| 证伪压力 | 毛利率、现金流、合同负债、存货等风险 | 压低 PEG 或限制年份切换 |  |  |

进入正式估值阶段时，先调用 `$financial-modeling` 生成 PEG-ready 与 DCF-ready 数据包；再由 `$growth-stock-valuation` 和 `dcf-model` 独立估值；最后可由 `$integrated-growth-valuation` 聚合。聚合输出不得倒灌进 `final_report` 形成目标价、目标市值、买卖建议或“当前贵不贵”的正式估值结论。

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

The handoff pair is not an estimate and not a model. It is the execution bridge from completed research to later `$financial-modeling`, `$growth-stock-valuation`, `dcf-model`, and `$integrated-growth-valuation`.

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

If either handoff is missing or older than `final_report`, downstream modeling and valuation skills must stop before formal valuation and request the post-report handoff pair.
