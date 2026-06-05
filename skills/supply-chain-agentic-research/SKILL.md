---
name: supply-chain-agentic-research
description: 独立主控供应链平台型成长股正式研究；用私有 modules、多角色/subagent、中间产物、进攻型市场交易变量、技术路线到价值量、原材料价格链、竞争/客户认证链、产能升级、订单经营验证、利润天花板、跟踪体系、两轮 QA 和投资人写作，完整覆盖 AI 算力、数据中心、新能源、机器人、先进封装、半导体设备/材料等供应链公司研究。Use when 用户需要深度分析供应链公司，判断身份切换、订单放量、技术路线升级、利润中枢上移、天花板抬升、市场预期差和证伪路径，并产出正式深度报告而非摘要。
---

# Agentic 供应链平台型成长股研究

## Overview

这是一个独立主控 skill，直接编排供应链平台型成长股研究的私有 modules，并通过多角色研究、中间文件、市场变量扩表、技术路线到价值量、原材料价格链、竞争/客户认证链、订单经营验证、利润桥、跟踪体系、两轮 QA 和投资人写作控制输出质量。`final_report` 是本 skill 的主终点；它负责把市场为什么交易公司、技术路线如何改变价值量、订单如何变收入、收入如何变利润、利润如何变现金流、哪些信号会让主线升级或证伪讲清楚。

本 skill 在研究阶段只沉淀两类研究接力候选输入；终稿 gate 通过后再生成两类正式研究接力文件：`dcf_financial_model_handoff` 交给 `$financial-modeling` 形成 PEG-ready 和 DCF-ready 数据包；`peg_valuation_handoff` 交给 `$growth-stock-valuation` 判断 PEG/动态 PE 的质性边界和 PEG 系数影响机制。正式 DCF 输入来自 `$financial-modeling` 输出的 DCF-ready 数据包，再交给 `dcf-model`；最后可由 `$integrated-growth-valuation` 聚合两个模型输出。`final_report` 不写目标价、目标市值、PE/PEG/SOTP、买卖评级或明确投资建议。

Token discipline:

- 不减少正式研究的角色和模块覆盖，但必须减少重复事实搬运。
- 同一事实只写入 `<prefix>_facts_core.md` 一次；后续中间稿用 `Fact-ID` 引用，不重复整段背景。
- 原始 CSV、问财长行、公告列表和 Gemini 长文不得被全文读入上下文；必须先抽取窄表或线索表。
- 三表和财务指标默认只取一个结构化数据源；只有接口失败、权限不可访问、字段缺失或明显异常时才 fallback 到其他源。
- Gemini/Google Search 只作为缺口型二次线索发现器，落盘为短线索表；不能用于公告财报、投关、三表、常规新闻或已由普通搜索覆盖的事实复述，不能写成长篇研究稿，也不能直接进入事实表。

核心判断是：

```text
产业周期够大 + 市场交易变量足够锐利 + 技术路线到价值量讲透 + 原材料/价格/产能传导清楚 + 竞争/客户认证链可验证 + 订单出货领先 + 第二曲线成型 + 利润平台换台阶 + 证据边界和证伪路径明确
```

## Naming Discipline

所有研究产物统一写入 `research_artifacts/<prefix>/`，文件名使用 `<prefix>_<artifact_key>.md`。`prefix` 是稳定的研究对象 ID，必须在 Step 1 前确定并写入 `<prefix>_question.md`；整轮任务不得中途改名。

单公司默认 prefix：`<market>_<code>_<short_name>`。A 股用 `A_300750_宁德时代`，港股用 `HK_00700_腾讯控股`，美股用 `US_NVDA_NVIDIA`；其他市场使用清晰市场短码。若用户显式给出 prefix，可以沿用，但必须能区分市场、代码和对象；若只给公司简称，先规范化为默认格式。

prefix 允许中文、英文字母、数字和下划线；空格、斜杠、冒号、括号、连字符、标点统一改为下划线，连续下划线压成一个。不要把日期放入常规 prefix；同一对象多次研究需要区分时，在末尾追加主题短码，例如 `A_300750_宁德时代_储能`。`artifact_key` 固定使用小写 `snake_case`，不得混用中文、空格、连字符或临时编号。

跨投研 skill 的通用命名固定如下：`question`、`facts_core`、`evidence_queue`、`evidence_index`、`market_variables_map`、`midterm_structure_review`、`skeptic_review`、`report_outline`、`final_report_expansion_plan`、`final_report`。投研到模型的接力文件只使用 `dcf_financial_model_handoff` 和 `peg_valuation_handoff`；`peg_valuation_deepdive`、`peg_valuation_scorecard`、`dcf_summary`、`dcf_model`、`dcf_validation`、`valuation_aggregate` 和 `valuation_scorecard` 只能由后续估值 skill 生成。

## When To Use

适合用户要求：

- 深度分析一只处在 AI 算力、数据中心、新能源、机器人、先进封装、半导体设备/材料等大产业周期中的供应链平台型公司。
- 判断公司是否发生身份切换、订单出货放量、产品代际升级、第二曲线成型、利润中枢上移和天花板抬升。
- 不只要核心结论，还要把产业周期、市场变量、技术路线到价值量、原材料传导、竞争客户链、产能升级、订单出货、第二曲线、利润桥和跟踪体系讲清楚。
- 需要用 subagent / 多角色 / 多阶段研究避免一次性摘要化输出。

不适合：

- 银行、地产、保险、纯消费品牌、纯软件互联网、早期创新药。
- 无收入利润底盘、只有概念没有订单和产能承接的题材股。
- 用户只要“一句话看法”。如果用户要求“快速判断”“先粗筛”，可以使用轻量模式，但必须说明未完成完整 agentic 流程。

## Non-Negotiables

正式研究必须同时满足以下要求：

0. 默认完成定义是写出并校验 `<prefix>_final_report.md`。除非用户明确说“只启动 subagent / 只要中间产物 / 先停在提纲 / 不要写终稿”，否则不能把“subagent 已完成”“QA 已完成”“可以进入 report_outline”或“中间文件已落盘”当作任务完成。任何缺口补写完成后，主控必须继续执行 `report_outline -> final_report_expansion_plan -> final_report -> final_report_gate.py`。
1. 完整覆盖 6 个主攻模块、3 个横向护栏模块、1 条技术路线横向 reference、1 个中期结构 QA、1 个终审事实 QA、1 个三表/FCF 建模 readiness、1 个 PEG 估值 readiness 和终稿 gate 后的两个正式 handoff：
   - 主攻模块：市场交易变量主线、架构/技术路线与天花板、原材料价格链、产能升级与第二曲线、订单出货与经营验证、利润天花板/利润桥。
   - 横向护栏模块：行业周期与供需格局、竞争格局与客户认证链、跟踪体系与警报信号。
   - 技术路线横向 reference：市场变量与技术路线到价值量链路。
   - QA：中期结构 QA 和终审事实 QA。
   - 研究阶段接力 readiness：三表/FCF 建模候选字段和 PEG 估值候选因子。
   - 终稿 gate 后正式接力输入：`dcf_financial_model_handoff` 和 `peg_valuation_handoff`。
2. 不允许直接输出终稿。必须先形成中间研究产物。
3. 每个核心判断必须写清楚：

```text
证据 -> 推理 -> 反证/替代解释 -> 判断强度
```

4. 必须区分公告或财报事实、客户/行业一手资料、订单/排产/出货口径、结构化行情和财务数据、市场口径、合理推断和情景假设。
5. 最终报告必须面向一般投资人，解释术语、铺设推理台阶，不能只堆概念、数据和结论。
6. 对市场正在交易但公告尚未充分验证的变量，不允许简单删除，也不允许只放在证据台账、脚注或反方审查里。必须降级保留为市场口径、券商假设、产业链线索或待验证变量，并写清证据等级、利润影响和验证路径。
7. 正文主线阶段不得过早压低变量。先把市场正在交易什么、技术路线为什么改变价值量、公司为什么能分到增量、利润如何变厚写清楚；最后再统一校准证据边界和验证路径。
8. 技术升级型供应链公司必须输出产品代际矩阵，并单独写价格与利润传导。不得只写“高端化”“结构升级”“国产替代”。
9. 利润桥必须从方向性升级为可计算或半可计算模型，至少拆收入、出货/产量、ASP/价值量、产品占比、毛利率、费用、折旧、良率、原材料、少数股东、投资收益、所得税、现金流和敏感性。
10. 若用户给出参考报告、PDF、研报或样稿，必须先做对标报告校准；正式终稿必须达到同类深度，或说明哪些部分因证据不足而不采用。
11. 搜索层必须高召回，但 Gemini 不作为常规事实采集入口。优先组合公告网站、交易所、公司官网、投资者关系、客户/竞品公告、券商研报摘要、行业机构、结构化数据、`$wencai-query`、`$tushare` 和普通 web search；只有在这些来源仍无法覆盖关键市场变量、客户/竞品链、技术路线或反证线索时，才检查 `GEMINI_API_KEY` 并运行 [scripts/gemini_google_search.py](scripts/gemini_google_search.py)。默认最多 1-2 组缺口型查询；若未运行，证据台账记录 `Gemini未运行原因：常规来源已覆盖/无关键缺口/不可用`。
12. `final_report` 不放正式估值章节，不写目标价、目标市值、PE/PEG/SOTP、买卖建议或“当前贵不贵”的估值结论；估值变量只能进入研究阶段 readiness、终稿 gate 后 handoff 或后续独立估值 skill。

## Research Posture

正式研究必须读取 [references/research-posture.md](references/research-posture.md)。主控层只保留姿态锚点：先写进攻型市场交易主线，再做证据分层；高重要市场变量不得因未公告验证而删除，必须写成“市场押注 -> 利润传导 -> 成立时升级 -> 不成立时降级 -> 验证指标”；章节标题优先包含变量、机制或结论方向。

## Agent Policy

正式研究必须读取 [references/agent-orchestration.md](references/agent-orchestration.md)。真实 subagent 是首选执行载体；若不可用，必须用分阶段文件化模拟独立角色，不得跳过角色。启动任何 subagent 前，主控必须传入最小 prompt packet：标的、任务目录、输出文件绝对路径、`question`、`facts_core`、`evidence_queue`、必要的 `evidence_index` 摘要、对应 `modules/*.md`、必要 reference、必写输出块和禁止项。已完成上游文件默认只传文件路径、相关 Fact-ID、200-400 字摘要或与本角色相关的片段，不全文塞入 prompt。

## Workflow

### Completion Contract

本 skill 的默认终点是 `final_report`，不是 subagent、QA、提纲或扩写蓝图。主控每次准备停止前必须做一次终点检查：

```text
1. 如果用户没有明确要求停在中间阶段，检查 `<prefix>_final_report.md` 是否已经写入。
2. 如果 `midterm_structure_review` 列出必须补写清单，先补写并记录补写结果，再进入 `report_outline`。
3. 如果 `report_outline` 不存在，写 `report_outline`。
4. 如果 `final_report_expansion_plan` 不存在，写 `final_report_expansion_plan`。
5. 如果 `final_report` 不存在，先读 `facts_core`、`report_outline`、`final_report_expansion_plan`、两轮 QA，再按章节按需读取中间文件片段并写 `final_report`。
6. 写完 `final_report` 后运行 `scripts/final_report_gate.py`；失败则补写并复跑。
7. 只有 `final_report` 存在且闸门通过，才可向用户说正式研究报告完成。
```

若用户只说“启动 subagent”，在本 skill 中默认解释为“用 subagent 执行完整正式研究流程”，而不是只完成多角色研究后停止；除非用户同时说“先别写终稿”“只要中间文件”或类似暂停指令。

### Step 0: 对标报告校准

如果用户提供 PDF、研报、样稿或明确说“按这篇深度报告的水平”，正式研究前必须先抽取参考报告结构，写入 `<prefix>_benchmark_calibration.md`。若用户没有提供具体参考报告，但要求“像参考报告一样优秀”“不要收敛”“写得像优秀深度报告”，则使用 [references/final-report.md](references/final-report.md) 和 [references/report-writing.md](references/report-writing.md) 的内置参考标准。

### Step 1: 建立研究目录

在当前任务目录下建立中间产物目录：

```text
research_artifacts/<prefix>/
  <prefix>_benchmark_calibration.md（如用户提供参考报告）
  <prefix>_question.md
  <prefix>_facts_core.md
  <prefix>_evidence_queue.md
  <prefix>_evidence_index.md
  <prefix>_market_variables_map.md
  <prefix>_industry_cycle_supply_demand.md
  <prefix>_architecture_value_ceiling.md
  <prefix>_product_generation_matrix.md
  <prefix>_competition_customer_chain.md
  <prefix>_raw_material_price_chain.md
  <prefix>_capacity_second_curve.md
  <prefix>_orders_business_validation.md
  <prefix>_profit_bridge.md
  <prefix>_tracking_dashboard.md
  <prefix>_dcf_financial_model_handoff.md（终稿 gate 后）
  <prefix>_peg_valuation_handoff.md（终稿 gate 后）
  <prefix>_midterm_structure_review.md
  <prefix>_skeptic_review.md
  <prefix>_report_outline.md
  <prefix>_final_report_expansion_plan.md
  <prefix>_final_report.md
```

所有中间产物、QA、post-report 估值接力文件和终稿必须写入上述目录；不得把投研文件写到任务根目录、`artifacts/` 或其他临时目录。本 skill 只生成到 `final_report` 以及终稿 gate 通过后的 `dcf_financial_model_handoff`、`peg_valuation_handoff` 为止；`peg_valuation_deepdive`、`dcf_model`、`valuation_aggregate` 等文件只能由后续独立 skill 生成。

### Step 2: 主线假设与适用性分诊

先写入 `<prefix>_question.md`：

- 市场正在交易什么：身份切换、订单放量、利润中枢上移、技术路线迭代、产品代际升级、原材料传导、第二曲线或市场变量兑现/证伪。
- 需要验证的 3 个核心问题。
- 先写进攻型主线假设：如果市场变量成立，利润天花板如何抬升；如果不成立，逻辑降级到哪一档。
- 公司是否适用供应链平台型框架；如不适用，停止完整流程并说明更合适框架。

### Step 3: 证据收集

写入 `<prefix>_evidence_index.md`，按 [references/data-path.md](references/data-path.md) 执行。证据台账必须识别市场变量和利润天花板变量；高重要变量必须传递到 `<prefix>_market_variables_map.md`、`<prefix>_report_outline.md` 和 `<prefix>_final_report.md`。

证据收集必须先写 `<prefix>_facts_core.md`，作为唯一事实中枢。`facts_core` 至少包含：

| Fact-ID | 字段/事件 | 数值/口径 | 报告期/日期 | 唯一事实来源 | 证据等级 | 进入哪些模块 |
| --- | --- | --- | --- | --- | --- | --- |

事实中枢规则：

- 财务三表、行情、市值、股本和财务指标默认只取一个结构化数据源；不要同时拉 Tushare、东方财富、AkShare 三套三表做常规交叉。
- 公告/投关/年报分业务数据以原文为准；结构化源只作定位和抽取辅助。
- 同一字段只能有一个 `唯一事实来源`。若后续发现冲突，新增一行 `口径冲突`，不要把两个数都写进正文。
- 每个 subagent 和中间稿只引用 `Fact-ID`，不得重复复制财报长表、公告原文大段或 Gemini 输出。

Gemini 不参与公告财报、投关、三表、行情、常规新闻和已知研报列表的重复搜索。只有普通搜索、本地资料和结构化数据仍无法覆盖关键变量时，才检查 `GEMINI_API_KEY` 并使用 [scripts/gemini_google_search.py](scripts/gemini_google_search.py) 做 1-2 组缺口型线索搜索；输出必须压缩写入 `<prefix>_evidence_queue.md`，最多保留 10-15 条线索：

| Lead-ID | 线索 | 来源/日期 | 核心说法 | 证据等级 | 是否已核验 | 需打开的原始来源 |
| --- | --- | --- | --- | --- | --- | --- |

Gemini/Google 搜索结果只能作为线索索引，必须回到原始公告、研报 PDF、公司/客户/竞品资料或结构化数据复核；未核验线索不得进入 `facts_core`。若未运行、不可用或脚本失败，必须在证据台账记录 `Gemini未运行原因`、错误信息和替代搜索路径。

### Step 3.5: 市场交易变量扩表

在分发研究角色前，先写入 `<prefix>_market_variables_map.md`。这是正式研究的方向盘，必须回答：市场当前最关心的 5-12 个变量是什么；每个变量来自哪里；为什么抬高天花板或改变利润斜率；若成立如何改变收入、ASP、毛利率、份额、现金流、少数股东权益或投资收益；若不成立逻辑降级成哪一档；哪个模块继续深挖；终稿哪个章节必须保留。

若标的处于技术路线快速迭代的供应链环节，必须建立通用链路：

```text
下游平台迭代 -> 性能瓶颈变化 -> 零部件/材料规格升级 -> 单机/单柜/单车/单套价值量、ASP、毛利率或用量变化 -> 供应商认证、份额、良率、产能约束 -> 订单、收入、利润和现金流兑现
```

详细方法见 [references/technology-route-value-chain.md](references/technology-route-value-chain.md)。

### Step 4: 多角色研究

正式研究中，主控必须覆盖 6 个主攻模块、3 个横向护栏模块、技术路线横向 reference、两类 handoff readiness、post-report handoff stage 和两轮 QA。模块文件保存在 `modules/` 目录下，是各角色的唯一详细 prompt 来源；模块覆盖不等于 subagent 数量，具体分组以 [references/agent-orchestration.md](references/agent-orchestration.md) 为准。

执行每个 subagent 或文件化阶段前，主控必须读取 [references/research-posture.md](references/research-posture.md)、[references/agent-orchestration.md](references/agent-orchestration.md) 和该 subagent 覆盖的一个或多个 `modules/*.md` 文件，并把其中的 `Purpose`、`Inputs`、`Workflow` 和 `Output` 放入 prompt packet。利润桥、跟踪体系、三表/FCF 建模 readiness 和 PEG 估值 readiness 必须按 [references/handoffs.md](references/handoffs.md) 执行；中期结构 QA 和终审事实 QA 必须按 [references/qa-gates.md](references/qa-gates.md) 执行。正式 handoff 文件只能在终稿 gate PASS 后生成。

主控必须在 `<prefix>_report_outline.md` 或终稿前保留一张覆盖表：

| 模块/护栏 | 必读模块/规则 | 输出文件 | 负责角色/阶段 | 结论强度 | 证据缺口 |
| --- | --- | --- | --- | --- | --- |
| 市场交易变量主线 | `modules/market-variables-spine.md` | `<prefix>_market_variables_map.md` | 市场变量 |  |  |
| 行业周期与供需格局 | `modules/industry-cycle-supply-demand.md` | `<prefix>_industry_cycle_supply_demand.md` | 行业周期/供需 |  |  |
| 架构/技术路线与天花板 | `modules/architecture-value-ceiling.md` + `references/technology-route-value-chain.md` | `<prefix>_architecture_value_ceiling.md`、`<prefix>_product_generation_matrix.md` | 架构/天花板 |  |  |
| 竞争格局与客户认证链 | `modules/competition-customer-chain.md` | `<prefix>_competition_customer_chain.md` | 竞争/客户链 |  |  |
| 原材料价格链 | `modules/raw-material-price-chain.md` | `<prefix>_raw_material_price_chain.md` | 原材料/价格 |  |  |
| 产能升级与第二曲线 | `modules/capacity-second-curve.md` | `<prefix>_capacity_second_curve.md` | 产能/第二曲线 |  |  |
| 订单出货与经营验证 | `modules/orders-business-validation.md` | `<prefix>_orders_business_validation.md` | 订单/经营验证 |  |  |
| 利润天花板/利润桥 | `modules/profit-bridge.md` + `references/handoffs.md` | `<prefix>_profit_bridge.md` | 利润桥 |  |  |
| 跟踪体系与警报信号 | `modules/tracking-dashboard.md` + `references/handoffs.md` | `<prefix>_tracking_dashboard.md` | 跟踪/证伪 |  |  |
| 三表/FCF 建模接力候选输入 | `references/handoffs.md` | 写入 `<prefix>_profit_bridge.md` / `<prefix>_evidence_grading.md` 的候选字段与缺口 | 三表/FCF readiness |  |  |
| PEG 估值接力候选输入 | `references/handoffs.md` | 写入 `<prefix>_tracking_dashboard.md` / `<prefix>_evidence_grading.md` 的 PEG 因子与缺口 | PEG readiness |  |  |
| 中期结构 QA | `references/qa-gates.md` | `<prefix>_midterm_structure_review.md` | 提纲前 QA |  |  |
| 终审事实 QA | `references/qa-gates.md` | `<prefix>_skeptic_review.md` | 终稿前 QA |  |  |

Step 4 完成后不得停止。若中期 QA 有缺口，补写完成后必须记录补写结果并继续 Step 5；若中期 QA 通过或补写后通过，必须继续写 `report_outline`、`final_report_expansion_plan` 和 `final_report`。

### Step 5: 写作提纲

写入 `<prefix>_report_outline.md`，不要直接写终稿。主控在写提纲前必须读取 [references/final-report.md](references/final-report.md) 和 [references/qa-gates.md](references/qa-gates.md)。提纲必须确认中期结构 QA 是否通过，列出市场真正交易的 3-8 个变量、上行情景触发器、产品代际/价值量、竞争/客户认证链、应保留表格和 10-14 个结论型章节，并初判终稿复杂度：`compact`、`standard`、`complex` 或 `long-form`。终稿前必须按 `qa-gates.md` 做市场变量覆盖 QA。

### Step 5.5: 终稿扩写蓝图

在写 `final_report.md` 前，必须先按 [references/final-report.md](references/final-report.md) 写 `<prefix>_final_report_expansion_plan.md`。扩写蓝图是防止终稿变成摘要的施工图，必须逐章绑定中间文件、列出 3-8 条必写素材、写清正文机制、变量增强/减弱、验证指标和复杂度 profile；扩写蓝图未完成，不允许写 `final_report.md`。

### Step 6: 面向普通投资人的终稿

写终稿前不要一次性读取全部中间文件。先读取 `<prefix>_facts_core.md`、`<prefix>_report_outline.md`、`<prefix>_final_report_expansion_plan.md`、`<prefix>_midterm_structure_review.md` 和 `<prefix>_skeptic_review.md`；再按扩写蓝图逐章按需读取对应模块片段。按 [references/report-writing.md](references/report-writing.md)、[references/final-report.md](references/final-report.md) 和 [references/qa-gates.md](references/qa-gates.md) 写 `<prefix>_final_report.md`。`report-writing.md` 只管正文写作风格；终稿结构、复杂度 profile、扩写蓝图和反摘要闸门以 `final-report.md` 为准。

终稿写作中，事实引用优先使用 `Fact-ID`，不要把中间稿里的同一事实重新展开多次；只有机制解释、变量增强/减弱和反方判断需要展开。

终稿完成后必须按 `qa-gates.md` 执行终稿 QA，并按 `final-report.md` 运行 `scripts/final_report_gate.py`；未通过时不得向用户宣称终稿完成，必须补写后复跑。正式版、发布版、对外版或 PDF/HTML 导出前的 publication hygiene 由 `qa-gates.md` 调用 `$research-report-publication-editor` 执行。

## Output Discipline

最终回复用户时，除非用户要求只看终稿，否则要说明：

- 新生成了哪些中间文件。
- 哪些 agent / 阶段完成了哪些任务。
- 6 个主攻模块、3 个横向护栏模块、两轮 QA、三表/FCF 建模 readiness、PEG 估值 readiness 和 post-report handoff stage 如何被覆盖。
- `final_report` 是否已经完成；若未完成，必须说明是用户明确要求暂停、闸门失败正在补写，还是遇到阻塞。不得在 `final_report.md` 缺失时说“研究完成”。
- 若触发正式版/发布版/PDF/HTML 导出，说明 `$research-report-publication-editor` 的 publication hygiene gate 是否通过；若未触发，说明尚未运行出版清理。
- 终稿文件路径。

最终回复前必须进行文件存在性检查：`<prefix>_final_report.md`、`<prefix>_report_outline.md` 和 `<prefix>_final_report_expansion_plan.md`。只要用户未明确要求停在中间阶段，任一缺失都必须继续补写，不应进入最终回复。

## References

- 数据路径与证据优先级：[references/data-path.md](references/data-path.md)
- 研究姿态与市场变量写法：[references/research-posture.md](references/research-posture.md)
- 多角色/subagent 编排：[references/agent-orchestration.md](references/agent-orchestration.md)
- 技术路线到价值量链路：[references/technology-route-value-chain.md](references/technology-route-value-chain.md)
- 投资人写作规范：[references/report-writing.md](references/report-writing.md)
- 接力产物与估值/三表桥：[references/handoffs.md](references/handoffs.md)
- QA 与出版闸门：[references/qa-gates.md](references/qa-gates.md)
- 终稿施工与反摘要闸门：[references/final-report.md](references/final-report.md)

## Valuation Handoff Execution Order Override

This section overrides any earlier workflow wording about valuation handoffs.

Do not produce formal valuation handoff files during the research-writing phase. The lead writer must finish `final_report`, `skeptic_review` must exist, and `scripts/final_report_gate.py` must return PASS first.

After that gate passes, launch one valuation-handoff subagent or equivalent post-report stage. It reads `final_report`, `skeptic_review`, `profit_bridge`, `tracking_dashboard`, `facts_core`, and only necessary supporting snippets, then writes exactly two formal handoffs:

```text
<prefix>_dcf_financial_model_handoff.md
<prefix>_peg_valuation_handoff.md
```

These files are the bridges from finished research to later modeling and valuation:

- `dcf_financial_model_handoff`: financial modeling inputs, PEG-ready candidate fields, DCF-ready / UFCF bridge requirements, and data gaps.
- `peg_valuation_handoff`: PEG factor treatment, scenario admission, quality discounts, year-switching limits, validation metrics, and prohibitions.

Both handoffs must include `handoff_status: final_report_passed`, source file paths, gate status, and generation time. Neither handoff may contain target price, target market cap, buy/sell language, or formal PEG / DCF conclusions.

The PEG handoff must explicitly explain coefficient mechanics. For every major factor, state whether it raises the PEG coefficient, lowers it, caps it, permits only an optimistic-case coefficient, blocks year switching, or has no coefficient effect yet. The explanation must connect evidence to coefficient treatment, not merely say "positive" or "negative".

If either formal handoff is missing or older than `final_report`, downstream valuation must stop and ask for the post-report handoff pair.
