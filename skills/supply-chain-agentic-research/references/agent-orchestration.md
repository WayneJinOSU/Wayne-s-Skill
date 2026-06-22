# Agent Orchestration

本文件承接主控的多角色/subagent 启动规则。正式研究必须读取本文件；若真实 subagent 可用，优先启动 subagent 分工；若不可用，必须用分阶段文件化方式模拟独立角色，不能跳过角色。

## Required Roles

正式研究必须覆盖 6 个主攻模块、3 个横向护栏模块、两类 handoff readiness、post-report handoff stage 和两轮 QA。模块覆盖不等于 subagent 数量。标准正式研究推荐按 `5 个研究 subagent + 2 个 QA subagent` 合并执行；复杂标的可以进一步拆分，但每个 module 的 Output 文件必须独立落盘。

标准分组如下：

| Subagent / 阶段 | 覆盖模块或规则 | 主要职责 | 必写输出 |
| --- | --- | --- | --- |
| 市场变量 / 行业周期 agent | `modules/market-variables-spine.md` + `modules/industry-cycle-supply-demand.md` | 市场正在交易什么、行业 beta 是否足够大、周期位置和供需缺口如何穿透到公司订单、ASP、毛利率和现金流 | `<标的>_market_variables_map.md`、`<标的>_industry_cycle_supply_demand.md` |
| 技术路线 / 竞争客户 agent | `modules/architecture-value-ceiling.md` + `modules/competition-customer-chain.md` + `references/technology-route-value-chain.md` | 终端平台/产品代际如何改变价值量、ASP、毛利率、认证门槛和份额；客户链和竞品能否验证公司可获得价值 | `<标的>_architecture_value_ceiling.md`、`<标的>_product_generation_matrix.md`、`<标的>_competition_customer_chain.md` |
| 原材料 / 产能第二曲线 agent | `modules/raw-material-price-chain.md` + `modules/capacity-second-curve.md` | 关键原材料、顺价、库存、毛利率留存、产能地图、高端/瓶颈/海外产能、第二曲线和归母口径 | `<标的>_raw_material_price_chain.md`、`<标的>_capacity_second_curve.md` |
| 订单经营验证 agent | `modules/orders-business-validation.md` | 订单、排产、出货、收入确认、利润释放、现金回收、客户 capex 穿透、供应链地位和承接动作验证 | `<标的>_orders_business_validation.md` |
| 利润桥 / 跟踪 / readiness agent | `modules/profit-bridge.md` + `modules/tracking-dashboard.md` + `references/handoffs.md` | 利润天花板、利润斜率、敏感性、红黄绿灯、三表/FCF 候选驱动、PEG 估值候选因子；只沉淀候选字段和缺口，不写正式 handoff | `<标的>_profit_bridge.md`、`<标的>_tracking_dashboard.md` |
| 中期结构 QA agent | `references/qa-gates.md` | 写提纲前检查行业、技术、竞争、客户、产能、订单、利润模型、跟踪体系、证据边界和市场变量正文保留 | `<标的>_midterm_structure_review.md` |
| 终审事实 QA / 反方审查 agent | `references/qa-gates.md` | 终稿前集中寻找证据缺口、替代解释、市场变量误用、把扩产当订单、把收入当利润、把市场口径当事实等问题 | `<标的>_skeptic_review.md` |

## Required Agent Outputs

每个研究 subagent 可以覆盖多个 modules，但每个 module 都必须按自己的 `Output` 段独立落盘，并输出本模块识别到的“市场变量交付块”和“上行情景交付块”。

Token discipline:

- 不减少 Required Roles，也不减少模块覆盖；优化只发生在输入和输出冗余控制。
- 每个角色必须优先读取 `<标的>_facts_core.md` 和 `<标的>_evidence_queue.md`。
- 已经进入 `facts_core` 的事实，只能用 `Fact-ID` 引用；除非需要解释口径冲突，不得重复复制财报表格、投关长段、公告列表或 Gemini 原文。
- 每个角色输出应聚焦“本角色新增判断、财务传导、反证和缺口”，不要重新写公司基本面背景。
- 如果必须新增事实，先写入或建议写入 `facts_core`，再在模块中引用。

市场变量交付块：

```text
变量：
市场口径：
证据等级：
成立时利润传导：
不成立时降级路径：
验证指标：
终稿保留方式：
```

上行情景交付块：

```text
上行变量：
利润传导：
触发条件：
降级条件：
验证指标：
终稿保留章节：
```

只要涉及产品代际、客户份额、ASP、毛利率、订单/排产、良率、核心客户认证、关键原料、产能利用率、单机价值量、第二曲线、少数股东权益或投资收益，即使证据弱，也要写清证据等级、成立/不成立时的财务传导和终稿保留方式。

## Subagent Prompt Packet

启动每个 subagent 时，主控必须传入一个最小 prompt packet，不能只给角色名：

- 标的名称/代码、任务目录、必须写入的一个或多个输出文件绝对路径。
- 必读输入文件：`question`、`facts_core`、`evidence_queue`、`evidence_index`、`market_variables_map`，以及该 subagent 覆盖的一个或多个 `modules/*.md` 文件。已完成的上游中间文件默认只传路径、相关 Fact-ID、200-400 字摘要或与本角色直接相关的片段；禁止把完整上游研究稿作为 prompt packet 的常规输入。
- 必读 reference：研究姿态读取 `references/research-posture.md`；技术路线读取 `references/technology-route-value-chain.md`；接力候选输入和 post-report 接力产物读取 `references/handoffs.md`；QA 读取 `references/qa-gates.md`；提纲、扩写蓝图和终稿读取 `references/final-report.md` 与 `references/report-writing.md`。
- 必须对覆盖的每个 module 分别输出“市场变量交付块”“上行情景交付块”“终稿保留方式”“证据缺口/降级路径”；若是 QA 角色，还必须按对应 reference 的表格骨架输出。正式 handoff 角色只允许在终稿 gate PASS 后启动。
- 禁止写目标价、目标市值、买卖建议或把市场口径伪装成公告事实。若文件不可读或信息不足，先列缺口、替代数据路径和可执行的情景边界，不得跳过角色。
- 禁止把 Gemini/Google Search 输出直接当作事实；只能引用已核验并写入 `facts_core` 的 Fact-ID，或引用 `evidence_queue` 的 Lead-ID 作为待核验线索。

## Fallback

如果当前环境、宿主规则或工具能力不允许真实 subagent，必须按同样的 `5+2` 分组用“分阶段文件化”的方式模拟独立研究角色：每个阶段单独产出文件，下一阶段读取文件后再继续，不要只在上下文里滚动压缩。

兜底流程不得停在研究文件。完成研究角色后必须继续：

```text
midterm_structure_review -> 缺口补写 -> report_outline -> final_report_expansion_plan -> final_report -> final_report_gate.py -> 失败补写并复跑
```

任何角色无法获取足够信息时，仍要输出市场正在交易的假设、缺少的数据、合理的情景边界和验证路径，不能跳过该角色。

## Post-Report Valuation Handoff Stage

估值接力不属于 `5+2` 研究 subagent 的中期产物。`final_report` 完成、`skeptic_review` 存在且 `scripts/final_report_gate.py` PASS 后，主控启动一个 valuation-handoff subagent 或等价文件化阶段。

该阶段读取 `final_report`、`skeptic_review`、`profit_bridge`、`tracking_dashboard`、`evidence_grading`、`facts_core` 和必要片段，写两个轻量接力文件：

```text
<prefix>_dcf_financial_model_handoff.md
<prefix>_peg_valuation_handoff.md
```

`peg_valuation_handoff` 必须单独说明 PEG 系数机制：每个主要因子到底是提高系数、降低系数、封顶、仅允许乐观情景、阻止年份切换，还是暂不影响。不得只写“利好/利空/正面/负面”。
