# Agent Orchestration

本文件承接主控的多角色/subagent 启动规则。正式研究必须读取本文件；若真实 subagent 可用，优先启动 subagent 分工；若不可用，必须用分阶段文件化方式模拟独立角色，不能跳过角色。

## Required Roles

正式研究必须触发多角色研究。市场重定价主线、旧业务底盘、第二曲线、行业经济性与蛋糕分配、平台复用、竞争/客户验证链、承接动作/经营验证、利润桥、跟踪体系、证据边界、终审事实 QA/反方审查这些研究/审查角色，以及中期进攻 QA，是质量控制机制，不是可选项。

模块覆盖不等于 subagent 数量。真实 subagent 是首选执行载体，但标准正式研究推荐按 `5 个研究 subagent + 2 个 QA subagent` 合并执行；不得把“10 个 modules”机械拆成 10 个碎片化 subagent。高复杂度、强争议或资料量很大的标的，可以进一步拆分某个研究组，但必须保持模块 Output 文件独立、市场变量交付独立、上行情景交付独立。

标准分组如下：

| Subagent / 阶段 | 覆盖模块或规则 | 主要职责 | 必写输出 |
| --- | --- | --- | --- |
| 市场重定价 / 第二曲线 agent | `modules/market-repricing-spine.md` + `modules/second-curve-ceiling.md` | 市场正在交易什么、身份切换在哪里、预期差来自哪里、新业务如何抬收入/毛利率/客户粘性/平台身份、哪些变量决定利润斜率；必须输出核心交易逻辑、市场误定价、稀缺资源/关键瓶颈、最小利润模型候选和验证点；不得把行业 TAM 直接写成公司利润 | `<标的>_investment_logic_card.md`、`<标的>_market_variables_map.md`、`<标的>_second_curve_ceiling.md` |
| 旧业务底盘 / 平台复用 agent | `modules/base-business-floor.md` + `modules/platform-reuse.md` | 收入利润、现金流、客户基础、行业地位、财务质量、下限支撑，以及技术/客户/工艺/产能/供应链/认证/组织能力如何复用 | `<标的>_base_business_floor.md`、`<标的>_platform_reuse.md` |
| 行业空间 / 竞争客户 agent | `modules/industry-space-share.md` + `modules/competition-customer-validation.md` | 行业为什么扩容、渗透率为何提升、TAM/SAM/SOM 如何分层、公司份额如何变化、客户验证处于哪一段、同行替代风险和公司优势来源 | `<标的>_industry_space_share.md`、`<标的>_competition_customer_validation.md` |
| 承接动作 / 利润桥 agent | `modules/execution-signals.md` + `modules/profit-bridge.md` + `references/handoffs.md` | 扩产、融资、设备、客户验证、订单、量产、研发投入、人员变化和现金流验证如何传导到旧业务利润、第二曲线利润、扩张成本、少数股东和三表/FCF 驱动；必须把最小利润模型细化成单位经济、数量乘数、兑现节奏、利润中枢区间和敏感性；只沉淀候选字段和缺口，不写正式 handoff | `<标的>_execution_signals.md`、`<标的>_profit_bridge.md` |
| 跟踪体系 / 证据边界 agent | `modules/tracking-dashboard.md` + `modules/evidence-grading.md` + `references/handoffs.md` | 把主线、行业经济性、份额变化和利润桥转成 2-4 个季度红黄绿灯、升级/降级条件、证伪触发，并把关键变量分成 A/B/C/D 证据等级；不得把重要市场变量简单删除 | `<标的>_tracking_dashboard.md`、`<标的>_evidence_grading.md` |
| 中期进攻 QA agent | `references/qa-gates.md` | 写终稿提纲前检查竞争客户链、行业 beta、行业经济性、TAM/SAM/SOM、公司份额、市场变量正文保留、上行情景、利润斜率、跟踪体系和证据边界；QA 的第一目标是把主线写厚，不是把变量删薄 | `<标的>_midterm_structure_review.md` |
| 终审事实 QA / 反方审查 agent | `references/qa-gates.md` | 终稿前集中寻找证据缺口、替代解释、市场变量误用、把扩产当订单、把收入当利润、普通投资人理解断点和证伪条件；只负责校准和证伪，不作为平权章节抢主线 | `<标的>_skeptic_review.md` |

## Required Agent Outputs

每个研究 subagent 可以覆盖多个 modules，但每个 module 都必须按自己的 `Output` 段独立落盘，并输出本模块识别到的“市场变量交付块”“上行情景交付块”和“核心逻辑校准块”。只要涉及新业务收入、客户份额、订单/量产、产品放量、毛利率、平台复用、研发团队、产能爬坡、核心资源或少数股东权益，即使证据弱，也要写清：市场口径说什么、证据等级、若成立如何改变收入/毛利率/费用率/现金流/利润中枢、若不成立逻辑降级成什么、影响最小利润模型的哪个参数、应在终稿哪个章节保留。若变量会改变核心交易逻辑、最大预期差、第一驱动参数或最小利润模型，必须同步更新或建议更新 `<标的>_investment_logic_card.md`。

Token discipline:

- 不减少 Required Roles，也不减少模块覆盖；优化只发生在输入和输出冗余控制。
- 主控在启动研究时先把静态 references/modules 压缩成 `execution_contract`；后续角色默认接收 contract 中与本角色相关的规则摘要，不重复全文读取同一 reference。
- 每个角色必须优先接收主控生成的 `role_packet`，其中只包含本角色相关的 `<标的>_facts_core.md` 行、`<标的>_evidence_queue.md` 行、必要 `evidence_index` 摘要、相关 Fact-ID/Lead-ID、直接相关片段和上游下游摘要块。
- 只有当 `role_packet` 出现口径冲突、证据不足、Fact-ID/Lead-ID 无法定位或 QA 闸门要求补写时，角色才回读完整 `facts_core`、`evidence_queue`、模块全文或原始来源。
- 已经进入 `facts_core` 的事实，只能用 `Fact-ID` 引用；除非需要解释口径冲突，不得重复复制财报表格、投关长段、公告列表、研报列表或 Gemini 原文。
- 每个角色输出应聚焦“本角色新增判断、财务传导、反证和缺口”，不要重新写公司基本面背景。
- 如果必须新增事实，先写入或建议写入 `facts_core`，再在模块中引用。
- 每个模块输出末尾必须写“下游摘要块”，供后续角色、提纲和终稿优先读取；下游摘要块不能替代模块正文，只是减少重复上下文传递。

上行情景交付块必须包含：

```text
上行变量：
利润传导：
触发条件：
降级条件：
验证指标：
终稿保留章节：
```

核心逻辑校准块必须包含：

```text
是否影响第一主线：
影响的利润模型参数：
第一/第二/第三驱动排序：
增强、校准还是证伪：
是否更新 investment_logic_card：
终稿处理：主段落/表格/跟踪/反方/删除
```

下游摘要块必须包含：

```text
关键结论：
涉及 Fact-ID：
涉及 Lead-ID：
影响的利润参数：
终稿保留方式：
仍需打开的原始来源：
建议下游只读片段：
```

## Subagent Role Packet

本节优化正式研究、QA 和终稿前阶段的上下文传递；正式 post-report valuation handoff 阶段仍按下方 `Post-Report Valuation Handoff Stage` 和 `references/handoffs.md` 执行，不在本轮改动范围内。

启动每个 subagent 时，主控必须传入一个最小 `role_packet`，不能只给角色名，也不能把完整上游文件作为常规输入：

- 标的名称/代码、任务目录、必须写入的一个或多个输出文件绝对路径。
- 本轮 `execution_contract` 中与该角色相关的规则摘要、禁止项和输出骨架；若 contract 不存在，主控必须先读取相关 reference/module 后生成，不得让每个角色重复读取静态规则全文。
- 必读输入切片：`question`、`investment_logic_card`（若已生成）的摘要或相关段落、`facts_core` 相关 Fact-ID 行、`evidence_queue` 相关 Lead-ID 行、必要 `evidence_index` 摘要，以及该 subagent 覆盖的一个或多个 `modules/*.md` 的 `Purpose/Inputs/Workflow/Output` 摘要。已完成的上游中间文件默认只传路径、相关 Fact-ID、下游摘要块、200-400 字摘要或与本角色直接相关的片段；禁止把完整上游研究稿作为 role packet 的常规输入。
- 必读 reference 的加载规则：研究姿态、QA、终稿写作等静态规则优先来自 `execution_contract`；只有 contract 缺失、规则冲突或角色需要未压缩细则时，才回读 `references/research-posture.md`、`references/qa-gates.md`、`references/final-report.md` 或 `references/report-writing.md`。
- 必须对覆盖的每个 module 分别输出“市场变量交付块”“上行情景交付块”“核心逻辑校准块”“终稿保留方式”“证据缺口/降级路径”；若是 QA 角色，还必须按对应 reference 的表格骨架输出。正式 handoff 角色只允许在终稿 gate PASS 后启动。
- 市场重定价 / 第二曲线 agent 必须写或更新 `<标的>_investment_logic_card.md`；承接动作 / 利润桥 agent 必须检查该卡中的最小利润模型是否需要修正，并在 `<标的>_profit_bridge.md` 记录修正结果。
- 禁止写目标价、目标市值、买卖建议或把市场口径伪装成公告事实。若文件不可读或信息不足，先列缺口、替代数据路径和可执行的情景边界，不得跳过角色。
- 禁止把 Gemini/Google Search 输出直接当作事实；只能引用已核验并写入 `facts_core` 的 Fact-ID，或引用 `evidence_queue` 的 Lead-ID 作为待核验线索。

## Fallback

如果当前环境、宿主规则或工具能力不允许真实 subagent，必须按同样的 `5+2` 分组用“分阶段文件化”的方式模拟独立研究角色：每个阶段单独产出文件，下一阶段读取文件后再继续，不要只在上下文里滚动压缩。不要把“无法启动真实 subagent”当作跳过角色的理由。

任何角色无法获取足够信息时，仍要输出市场正在交易的假设、缺少的数据、合理的情景边界和验证路径，不能跳过该角色。

## Post-Report Valuation Handoff Stage

正式估值接力不属于 `5+2` 研究 subagent 的中期产物。`final_report` 完成、`skeptic_review` 存在且 `scripts/final_report_gate.py` PASS 后，主控再启动一个 valuation-handoff subagent 或等价文件化阶段。

该阶段读取 `final_report`、`skeptic_review`、`profit_bridge`、`tracking_dashboard`、`evidence_grading`、`facts_core` 和必要片段，写且只写两个正式接力文件：

```text
<prefix>_dcf_financial_model_handoff.md
<prefix>_peg_valuation_handoff.md
```

`peg_valuation_handoff` 必须单独说明 PEG 系数机制：每个主要因子到底是提高系数、降低系数、封顶、仅允许乐观情景、阻止年份切换，还是暂不影响。不得只写“利好/利空/正面/负面”。
