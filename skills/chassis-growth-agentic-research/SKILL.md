---
name: chassis-growth-agentic-research
description: 独立主控底盘型成长股正式研究；用私有 modules、多角色/subagent、中间产物、进攻型市场重定价主线、行业经济性与蛋糕分配、竞争/客户验证链、中期进攻 QA、终审事实 QA 和投资人写作，完整覆盖旧业务底盘、第二成长曲线、TAM/SAM/SOM、平台复用、承接动作、利润桥、跟踪体系、证据边界、三表/FCF 建模接力输入和估值接力输入。Use when 用户需要深度分析 A 股制造业、AI算力、数据中心、新能源、机器人、先进制造、半导体设备/材料等底盘型成长公司，判断旧业务托底、行业经济性拐点、新业务抬天花板、公司份额提升、平台能力复用、竞争客户验证、利润中枢上移、预期差和证伪路径，并产出正式深度报告而非摘要。
---

# Agentic 底盘型成长股研究

## Overview

这是一个独立主控 skill，直接编排底盘型成长股研究的私有 modules，并通过多角色研究、中间文件、进攻型市场重定价主线、行业经济性与蛋糕分配、竞争/客户验证链、中期进攻 QA、利润桥、跟踪体系、终审事实 QA 和投资人写作控制输出质量。`final_report` 是本 skill 的主终点；它先把市场为什么重新定价、上行变量如何传导到利润斜率讲完整，再由证据边界和反方审查校准收敛。终稿负责把旧业务底盘、行业为什么扩容、公司为什么能分到蛋糕、第二曲线把上限抬到哪里、平台复用为什么让跨界可信、竞争客户验证如何支撑份额、承接动作如何变成收入利润、利润中枢和证伪路径讲清楚。正式三表/FCF 建模、PEG 估值、DCF 估值和聚合由 `$financial-modeling`、`$growth-stock-valuation`、`dcf-model` 与 `$integrated-growth-valuation` 接手；本 skill 在研究阶段只沉淀接力候选输入，终稿 gate 通过后再准备两类正式研究接力文件：`dcf_financial_model_handoff` 给三表/FCF、PEG-ready 和 DCF-ready 驱动，`peg_valuation_handoff` 给 PEG/动态 PE 的质性边界和 PEG 系数影响机制。DCF 不设投研侧平级 handoff，由 `$financial-modeling` 输出 DCF-ready 数据包后交给 `dcf-model`，本 skill 不写目标价、目标市值、PE/PEG/SOTP、买卖评级或明确投资建议。

Token discipline:

- 不减少正式研究的角色和模块覆盖；只减少重复事实搬运、重复取数和长文件全文读取。
- 同一事实只写入 `<prefix>_facts_core.md` 一次；后续中间稿、handoff 和终稿优先用 `Fact-ID` 引用。
- 原始 CSV、问财长行、公告列表、研报列表和 Gemini 长文不得被全文读入上下文；必须先抽取窄表、短摘要或线索表。
- 三表、财务指标、行情、市值和股本默认只取一个结构化数据源；只有接口失败、权限不可访问、关键字段缺失或明显异常时才 fallback 到其他源。
- Gemini/Google Search 只作为缺口型二次线索发现器，落盘为 `<prefix>_evidence_queue.md`；不能用于公告财报、投关、三表、常规新闻或已由普通搜索覆盖的事实复述，不能写成长篇研究稿，也不能直接进入事实表。
- subagent prompt packet 默认只传 `facts_core`、`evidence_queue`、必要的 `evidence_index` 摘要、相关 Fact-ID、模块规则和直接相关片段；不把完整上游研究稿塞进 prompt。

核心判断是：

```text
旧业务底盘够硬 + 市场重定价变量清楚 + 行业经济性改善带来渗透率提升 + TAM/SAM/SOM 不混用 + 公司份额提升路径清楚 + 第二曲线抬高天花板 + 平台能力可复用 + 竞争客户验证不缺位 + 承接动作进入经营兑现 + 利润桥走通 + 证据边界和证伪路径明确
```

本 skill 的目标不是生成高密度摘要，也不是把模块框架机械填满，而是通过多角色研究和中间产物，产出普通投资人能读懂、投资人能跟踪、反方能检验的正式研究报告：市场为什么重新定价，公司旧业务给了什么下限，行业为什么扩容，行业增长的钱为什么不是所有人平分，公司凭什么拿更多，第二曲线把上限抬到哪里，平台复用为什么让跨界可信，客户和竞争证据如何验证新身份，承接动作如何变成收入和利润，利润桥在哪些变量上变陡，哪些信号会让主线升级或证伪。

## Naming Discipline

所有研究产物统一写入 `research_artifacts/<prefix>/`，文件名使用 `<prefix>_<artifact_key>.md`。`prefix` 是稳定的研究对象 ID，必须在 Step 1 前确定并写入 `<prefix>_question.md`；整轮任务不得中途改名。

单公司默认 prefix：`<market>_<code>_<short_name>`。A 股用 `A_300750_宁德时代`，港股用 `HK_00700_腾讯控股`，美股用 `US_NVDA_NVIDIA`；其他市场使用清晰市场短码。若用户显式给出 prefix，可以沿用，但必须能区分市场、代码和对象；若只给公司简称，先规范化为默认格式。

prefix 允许中文、英文字母、数字和下划线；空格、斜杠、冒号、括号、连字符、标点统一改为下划线，连续下划线压成一个。不要把日期放入常规 prefix；同一对象多次研究需要区分时，在末尾追加主题短码，例如 `A_300750_宁德时代_储能`。`artifact_key` 固定使用小写 `snake_case`，不得混用中文、空格、连字符或临时编号。

跨投研 skill 的通用命名固定如下：`question`、`facts_core`、`evidence_queue`、`evidence_index`、`market_variables_map`、`midterm_structure_review`、`skeptic_review`、`report_outline`、`final_report_expansion_plan`、`final_report`。投研到模型的接力文件只使用 `dcf_financial_model_handoff` 和 `peg_valuation_handoff`；`peg_valuation_deepdive`、`peg_valuation_scorecard`、`dcf_summary`、`dcf_model`、`dcf_validation`、`valuation_aggregate` 和 `valuation_scorecard` 只能由后续估值 skill 生成。

## When to use

适合用户要求：

- 深度分析一只 A 股制造业、AI 算力、数据中心、新能源、机器人、先进制造、半导体设备/材料等底盘型成长公司。
- 判断公司是否发生身份切换、行业经济性拐点、第二成长曲线成型、份额提升、平台能力复用、竞争客户验证、订单/客户/产能承接、利润中枢上移，并把证据、推理、市场口径和证伪点讲清楚。
- 不只要核心结论，还要把旧业务底盘、行业经济性与蛋糕分配、新业务天花板、平台复用、承接动作、利润桥和后续跟踪讲清楚。
- 需要用 subagent / 多角色 / 多阶段研究避免一次性摘要化输出。

不适合：

- 银行、地产、保险、纯资源周期、早期创新药、纯消费品牌。
- 无收入利润底盘、只有概念没有客户/订单/产能/研发承接的题材股。
- 用户只要“一句话看法”。如果用户要求“快速判断”“先粗筛”，可以使用轻量模式，但必须说明未完成完整 agentic 流程。

## Non-negotiables

正式研究必须同时满足以下要求：

0. 默认完成定义是写出并校验 `<prefix>_final_report.md`。除非用户明确说“只启动 subagent / 只要中间产物 / 先停在提纲 / 不要写终稿”，否则不能把“subagent 已完成”“QA 已完成”“可以进入 report_outline”或“中间文件已落盘”当作任务完成。任何缺口补写完成后，主控必须继续执行 `report_outline -> final_report_expansion_plan -> final_report -> final_report_gate.py`。如果最终回复用户时 `final_report.md` 不存在，必须明确说明这是用户要求暂停或任务被阻塞，不能用“研究完成”表述。
1. 完整覆盖 7 个核心私有研究模块、3 个横向护栏模块、1 个中期进攻 QA、1 个终审事实 QA、1 个三表/FCF 建模 readiness、1 个 PEG 估值 readiness 和终稿 gate 后的两个正式 handoff：
   - 市场重定价主线
   - 旧业务底盘
   - 第二成长曲线
   - 行业经济性与蛋糕分配
   - 平台复用能力
   - 承接动作
   - 利润桥
   - 横向护栏：竞争/客户验证链
   - 横向护栏：跟踪体系
   - 横向护栏：证据边界与验证路径
   - 中期进攻 QA：检查是否缺行业 beta、竞争客户链、市场变量、上行情景、利润斜率、跟踪体系、证据边界和终稿主线
   - 终审事实 QA：反方审查、事实边界、替代解释和证伪检查，只负责校准，不负责削弱主线气势
   - 三表/FCF 建模 readiness：研究阶段只沉淀 `$financial-modeling` 可用的收入、毛利率、费用率、capex、营运资本、税率、利息、UFCF、PEG-ready 候选字段和 DCF-ready 候选字段；正式 `dcf_financial_model_handoff` 在终稿 gate 通过后生成
   - PEG 估值 readiness：研究阶段只沉淀 PEG/动态 PE 所需的利润锚边界、核心因子、情景准入、质量折价、年份切换和证伪规则；正式 `peg_valuation_handoff` 在终稿 gate 通过后生成，并单独说明 PEG 系数影响机制；不写估值结论
   研究模块由本 skill 私有管理，模块文件放在 `modules/` 目录下；中期进攻 QA 不单独做 module，写入 `<prefix>_midterm_structure_review.md`。本 skill 不再调用或依赖外部 common 模块。正式估值阶段依次由 `$financial-modeling` 生成 PEG-ready/DCF-ready，再由 `$growth-stock-valuation` 和 `dcf-model` 独立估值，最后由 `$integrated-growth-valuation` 聚合。
2. 不允许直接输出终稿。必须先形成中间研究产物。
3. 每个核心判断必须写清楚：

```text
证据 -> 推理 -> 反证/替代解释 -> 判断强度
```

4. 必须区分：
   - 公告或财报事实
   - 结构化行情和财务数据
   - 客户、订单、产能或行业一手资料
   - 市场口径
   - 合理推断
   - 情景假设
5. 最终报告必须面向一般投资人，解释术语、铺设推理台阶，不能只堆结论、概念和表格。
6. 对市场正在交易但公告尚未充分验证的变量，不允许简单删除，也不允许只放在证据台账、脚注或反方审查里。必须降级保留为市场口径、券商假设、产业链线索或待验证变量，并写清证据等级、利润影响和验证路径。
7. 不要在正文主线阶段过早压低变量。先把市场正在交易什么、行业为什么扩容、公司为什么能分到蛋糕、利润如何变厚写清楚；最后再统一校准证据边界和验证路径。证据分层服务于判断，不替代判断。
8. 终稿必须先建立进攻型重定价主线：市场到底在押什么，公司为什么不只是旧业务修复或普通题材映射，哪些变量会让利润斜率变陡，公告事实验证了哪一段，下一季看什么来确认。不得把高重要市场变量先写成“证据不足、后续关注”后就结束。
9. 第二成长曲线必须回答“抬收入、抬毛利率、抬客户粘性、抬平台身份，还是只抬题材热度”。不得把行业空间直接等同于公司利润。
10. 行业经济性与蛋糕分配必须回答：行业扩容来自成本下降、效率提升、性能突破、认证完成、客户批量导入、供给瓶颈解除还是政策/资本开支；TAM 只说明想象空间，SAM 说明可服务方向，SOM 才允许进入公司收入和利润桥。
11. 平台复用必须拆技术、客户、工艺、产能、供应链、认证体系、组织能力和经济性曲线。不能只写“协同”“平台化”“复用能力强”。
12. 承接动作必须区分扩产、融资、设备、客户验证、订单、量产和财报兑现。扩产不是订单，订单不是利润，收入增长不是利润中枢永久上移。
13. 竞争/客户验证链必须回答：竞争对手是否也能拿到同一新业务机会、客户验证处于送样/认证/小批/量产/份额提升哪一段、公司优势来自技术、成本、交付、客户关系、认证周期还是平台复用。不得只写“客户优质、竞争格局好”。
14. 利润桥默认做轻量利润中枢和利润斜率，不替代正式估值。必须拆清旧业务底盘利润、行业扩容中公司可获取份额、第二曲线新增利润、平台复用收益、扩张费用/折旧/财务成本/爬坡损耗、少数股东权益和现金流质量。
15. 中期进攻 QA 和终审事实 QA 不得把报告重新拉回保守摘要。中期 QA 首先检查“上行变量、利润斜率、客户份额、毛利率弹性、第二曲线天花板和跟踪触发器是否写透”；终审 QA 再检查事实边界、替代解释和证伪条件。
16. 搜索层必须高召回，但 Gemini 不作为常规事实采集入口。优先组合公告网站、交易所、公司官网、投资者关系、客户/竞品公告、券商研报摘要、行业机构、结构化数据、`$wencai-query`、`$tushare` 和普通 web search；只有这些来源仍无法覆盖关键市场变量、客户/竞品链、行业经济性或反证线索时，才检查 `GEMINI_API_KEY` 并运行 [scripts/gemini_google_search.py](scripts/gemini_google_search.py)。默认最多 1-2 组缺口型查询；若未运行，证据台账记录 `Gemini未运行原因：常规来源已覆盖/无关键缺口/不可用`。Gemini/Google 搜索结果只能进入证据台账的“市场口径/线索”层，必须回到原始公告、研报 PDF、公司/客户/竞品资料或结构化数据复核后，才能支撑正文判断。
17. `final_report` 不放正式估值章节，不写目标价、目标市值、PE/PEG/SOTP、买卖建议或“当前贵不贵”的估值结论；终稿 gate 通过后的 `peg_valuation_handoff` 也不得输出这些结论，只能作为后续 PEG 估值 skill 的因子接口、消费规则和 PEG 系数机制说明。三表/FCF 驱动、PEG-ready 候选字段和 DCF-ready 候选字段进入终稿 gate 通过后的 `dcf_financial_model_handoff`，由 Financial Modeling 产出 PEG-ready 与 DCF-ready 两个数据包。

## Research Posture

正式研究必须读取 [references/research-posture.md](references/research-posture.md)。主控层只保留姿态锚点：先写进攻型重定价主线，再做证据分层；高重要市场变量不得因未公告验证而删除，必须写成“市场押注 -> 利润传导 -> 成立时升级 -> 不成立时降级 -> 验证指标”；章节标题优先包含变量、机制或结论方向。

## Agent Policy

正式研究必须读取 [references/agent-orchestration.md](references/agent-orchestration.md)。真实 subagent 是首选执行载体；若不可用，必须用分阶段文件化模拟独立角色，不得跳过角色。启动任何 subagent 前，主控必须传入最小 prompt packet：标的、任务目录、输出文件绝对路径、`question`、`facts_core`、`evidence_queue`、必要的 `evidence_index` 摘要、对应 `modules/*.md`、必要 reference、必写输出块和禁止项。已完成上游文件默认只传文件路径、相关 Fact-ID、200-400 字摘要或与本角色相关的片段。

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

若用户只说“启动 subagent”，在本 skill 中默认解释为“用 subagent 执行完整正式研究流程”，而不是只完成 Step 4 后停止；除非用户同时说“先别写终稿”“只要中间文件”或类似暂停指令。

### Step 1: 建立研究目录

在当前任务目录下建立中间产物目录：

```text
research_artifacts/<prefix>/
  <prefix>_question.md
  <prefix>_facts_core.md
  <prefix>_evidence_queue.md
  <prefix>_evidence_index.md
  <prefix>_market_variables_map.md
  <prefix>_base_business_floor.md
  <prefix>_second_curve_ceiling.md
  <prefix>_industry_space_share.md
  <prefix>_platform_reuse.md
  <prefix>_competition_customer_validation.md
  <prefix>_execution_signals.md
  <prefix>_profit_bridge.md
  <prefix>_tracking_dashboard.md
  <prefix>_evidence_grading.md（证据边界与验证路径）
  <prefix>_dcf_financial_model_handoff.md（终稿 gate 后三表/FCF 建模接力输入）
  <prefix>_peg_valuation_handoff.md（终稿 gate 后 PEG 估值接力输入）
  <prefix>_midterm_structure_review.md
  <prefix>_skeptic_review.md
  <prefix>_report_outline.md
  <prefix>_final_report_expansion_plan.md
  <prefix>_final_report.md
```

所有中间产物、QA、post-report 估值接力文件和终稿必须写入上述目录；不得把投研文件写到任务根目录、`artifacts/` 或其他临时目录。

### Step 2: 主线假设与适用性分诊

先写入 `<prefix>_question.md`：

- 市场正在交易什么：身份重估、第二曲线、行业经济性改善、渗透率提升、公司份额变化、利润中枢上移、订单兑现、旧业务错杀修复或平台能力复用。
- 需要验证的 3 个核心问题。
- 先写“进攻型主线假设”：如果市场变量成立，利润中枢如何上移；如果不成立，逻辑降级到哪一档。
- 公司是否适用底盘型成长股框架；如不适用，停止完整流程并说明更合适框架。

### Step 3: 证据收集

写入 `<prefix>_evidence_index.md`，按可获得性覆盖。证据收集必须先写 `<prefix>_facts_core.md`，作为唯一事实中枢；同一字段只能保留一个事实来源，若后续发现冲突，新增“口径冲突/待复核”行，不把两个数都反复写进正文。

`facts_core` 至少包含：

| Fact-ID | 字段/事件 | 数值/口径 | 报告期/日期 | 唯一事实来源 | 证据等级 | 进入哪些模块 |
| --- | --- | --- | --- | --- | --- | --- |

- 公告原文：年报、季报、业绩预告/快报、募投、定增/可转债、重大合同、关联交易、问询回复、业绩说明会。
- 结构化数据：默认选择一个结构化源拉行情、市值、财务三表、财务指标、现金流、历史行情；市值和估值类字段只用于市场阶段判断、研究阶段候选字段、post-report `peg_valuation_handoff` 或后续估值模型输入，不在终稿形成正式估值结论。只有失败、不可访问、缺字段或明显异常才 fallback。
- 市场位置：`$wencai-query` 查概念、同行排名、题材口径、阶段涨幅、市场关注点。
- 公司官网、交易所互动、投资者关系、客户/竞品公告、行业资料和可靠新闻。
- 市场增量情报：券商研报核心假设、产业链调研、专家问答、交易热词、新业务客户和竞品进展。此类资料不能直接等同事实，但必须用于识别市场真正交易的边际变量。
- 行业空间与份额口径：券商/行业报告里的 TAM/SAM/SOM、渗透率、价格/成本/效率曲线、供需缺口、竞争份额和利润率假设。此类数据必须标注来源和口径，但不能因不是公告事实就从主线删除。
- Gemini Google Search 缺口型增强：公告财报、投关、三表、行情、常规新闻和已知研报列表不使用 Gemini 重复搜索。只有普通搜索、本地资料和结构化数据仍无法覆盖市场重定价变量、行业经济性/TAM/SAM/SOM、客户/竞品验证、平台复用、承接动作或利润桥关键缺口时，才检查 `GEMINI_API_KEY` 并使用 `scripts/gemini_google_search.py`，默认最多 1-2 组最相关查询；若未运行、不可用或脚本失败，必须在本台账记录 `Gemini未运行原因`、错误信息和替代搜索路径。输出必须压缩写入 `<prefix>_evidence_queue.md`，最多保留 10-15 条线索；不得把模型总结直接当事实，未核验线索不得进入 `facts_core`。

`evidence_queue` 至少包含：

| Lead-ID | 线索 | 来源/日期 | 核心说法 | 证据等级 | 是否已核验 | 需打开的原始来源 |
| --- | --- | --- | --- | --- | --- | --- |

证据台账必须识别“市场变量”，但表格只能作为索引或 QA，不能替代正文推理。对每个高重要市场变量，必须写清：变量、市场口径、证据等级、成立时利润传导、不成立时降级路径、验证指标和终稿保留方式。

### Step 4: 多角色研究

正式研究中，主控必须覆盖 7 个核心私有研究模块、3 个横向护栏模块、1 个中期进攻 QA、1 个终审事实 QA、三表/FCF 建模 readiness、PEG 估值 readiness 和终稿 gate 后的正式 handoff stage。核心模块负责主线成稿，横向护栏负责嵌入式检查和变量校准，不要求在终稿中逐一单独成章。模块文件保存在 `modules/` 目录下，是各角色的唯一详细 prompt 来源；这些模块是 `chassis-growth-agentic-research` 的私有模块，不作为独立 skill 暴露。模块覆盖不等于 subagent 数量；标准正式研究按 `5 个研究 subagent + 2 个 QA subagent` 合并执行，具体分组以 [references/agent-orchestration.md](references/agent-orchestration.md) 为准。

执行每个 subagent 或文件化阶段前，主控必须读取 [references/research-posture.md](references/research-posture.md)、[references/agent-orchestration.md](references/agent-orchestration.md) 和该 subagent 覆盖的一个或多个 `modules/*.md` 文件，并把其中的 `Purpose`、`Inputs`、`Workflow` 和 `Output` 放入 prompt packet；不得只依赖下表的角色名或主控摘要。每个模块都必须按自己的 `Output` 段写入指定文件，并输出“市场变量交付”和“上行情景交付”。

主控必须在 `<prefix>_report_outline.md` 或终稿前保留一张覆盖表：

| 模块/护栏 | 必读模块/规则 | 输出文件 | 负责角色/阶段 | 结论强度 | 证据缺口 |
| --- | --- | --- | --- | --- | --- |
| 市场重定价主线 | `modules/market-repricing-spine.md` | `<prefix>_market_variables_map.md` | 市场重定价 |  |  |
| 旧业务底盘 | `modules/base-business-floor.md` | `<prefix>_base_business_floor.md` | 旧业务底盘 |  |  |
| 第二成长曲线 | `modules/second-curve-ceiling.md` | `<prefix>_second_curve_ceiling.md` | 第二曲线 |  |  |
| 行业经济性与蛋糕分配 | `modules/industry-space-share.md` | `<prefix>_industry_space_share.md` | 行业空间/份额 |  |  |
| 平台复用能力 | `modules/platform-reuse.md` | `<prefix>_platform_reuse.md` | 平台复用 |  |  |
| 竞争/客户验证链 | `modules/competition-customer-validation.md` | `<prefix>_competition_customer_validation.md` | 竞争/客户验证 |  |  |
| 承接动作 | `modules/execution-signals.md` | `<prefix>_execution_signals.md` | 承接/经营验证 |  |  |
| 利润桥 | `modules/profit-bridge.md` + `references/handoffs.md` | `<prefix>_profit_bridge.md` | 利润桥 |  |  |
| 跟踪体系 | `modules/tracking-dashboard.md` + `references/handoffs.md` | `<prefix>_tracking_dashboard.md` | 跟踪/证伪 |  |  |
| 证据边界与验证路径 | `modules/evidence-grading.md` + `references/handoffs.md` | `<prefix>_evidence_grading.md` | 证据边界 |  |  |
| 三表建模接力候选输入 | `references/handoffs.md` | 写入 `<prefix>_profit_bridge.md` / `<prefix>_evidence_grading.md` 的候选字段与缺口 | 三表/FCF readiness |  |  |
| PEG 估值接力候选输入 | `references/handoffs.md` | 写入 `<prefix>_tracking_dashboard.md` / `<prefix>_evidence_grading.md` 的 PEG 因子与缺口 | PEG readiness |  |  |
| 中期进攻 QA | `references/qa-gates.md` | `<prefix>_midterm_structure_review.md` | 提纲前 QA |  |  |
| 终审事实 QA | `references/qa-gates.md` | `<prefix>_skeptic_review.md` | 终稿前 QA |  |  |

利润桥、跟踪体系、证据边界和估值接力候选输入必须按 [references/handoffs.md](references/handoffs.md) 执行；主控在写这些文件前必须读取该 reference。Step 4 不写正式 `dcf_financial_model_handoff` 或 `peg_valuation_handoff`，只在利润桥、跟踪体系和证据边界文件中沉淀后续可消费的候选字段、因子、证据等级和缺口。正式 `dcf_financial_model_handoff` 只把终稿后的投研变量翻译成 `$financial-modeling` 可用的三表/FCF、PEG-ready 和 DCF-ready 驱动；正式 `peg_valuation_handoff` 只把终稿后的投研因子翻译成 PEG/动态 PE 可消费的利润锚边界、情景准入、年份切换、质量折价和 PEG 系数影响机制；它们都不重建三表、不自填正式预测、不输出目标价、目标市值、买卖建议或最终估值结论。

若用户在同一任务中继续调用 `$integrated-growth-valuation`，聚合输出由估值聚合器写入 `<prefix>_valuation_aggregate.md` 和 `<prefix>_valuation_scorecard.md`；本 skill 只在跟踪体系中吸收其证伪阈值，不生成这些文件，也不得倒灌进 `final_report` 形成目标价、目标市值、买卖建议或“当前贵不贵”的正式估值结论。

中期进攻 QA 和终审事实 QA 必须按 [references/qa-gates.md](references/qa-gates.md) 执行。中期 QA 写入 `<prefix>_midterm_structure_review.md`，在写终稿提纲前检查模块缺口、进攻型主线、上行情景、利润斜率、跟踪体系、证据边界和终稿主线；若发现缺口，必须列出“必须补写清单”，主控补完后才能写 `final_report`。中期 QA 不要求正式 handoff 文件存在。终审事实 QA/反方审查写入 `<prefix>_skeptic_review.md`，它只校准证据边界和证伪点，不负责削弱主线气势，也不得把高重要市场变量简单删回风险提示。

Step 4 完成后不得停止。若中期 QA 有缺口，补写完成后必须记录补写结果并继续 Step 5；若中期 QA 通过或补写后通过，必须继续写 `report_outline`、`final_report_expansion_plan` 和 `final_report`。

### Step 5: 写作提纲

写入 `<prefix>_report_outline.md`，不要直接写终稿。主控在写提纲前必须读取 [references/final-report.md](references/final-report.md) 和 [references/qa-gates.md](references/qa-gates.md)。提纲必须确认中期进攻 QA 是否通过，列出市场真正交易的 3-8 个变量、上行情景触发器、TAM/SAM/SOM 分层、竞争/客户验证链、应保留表格和 8-12 个结论型章节，并初判终稿复杂度：`compact`、`standard`、`complex` 或 `long-form`。终稿前必须按 `qa-gates.md` 做市场变量覆盖 QA。

### Step 5.5: 终稿扩写蓝图

在写 `final_report.md` 前，必须先按 [references/final-report.md](references/final-report.md) 写 `<prefix>_final_report_expansion_plan.md`。扩写蓝图是防止终稿变成摘要的施工图，必须逐章绑定中间文件、列出 3-8 条必写素材、写清正文机制、变量增强/减弱、验证指标和复杂度 profile；扩写蓝图未完成，不允许写 `final_report.md`。

### Step 6: 面向普通投资人的终稿

写终稿前不要一次性读取全部中间文件。先读取 `<prefix>_facts_core.md`、`<prefix>_report_outline.md`、`<prefix>_final_report_expansion_plan.md`、`<prefix>_midterm_structure_review.md` 和 `<prefix>_skeptic_review.md`；再按扩写蓝图逐章按需读取对应模块片段。按 [references/report-writing.md](references/report-writing.md)、[references/final-report.md](references/final-report.md) 和 [references/qa-gates.md](references/qa-gates.md) 写 `<prefix>_final_report.md`。`final_report` 是主笔重构，不是模块摘要；核心章节必须使用 Markdown H2 标题 `##`，默认 `standard` 模式为 8,000-12,000 中文字，`compact`、`complex`、`long-form` 的适用条件和闸门 profile 以 `final-report.md` 为准。事实引用优先使用 `Fact-ID`，机制、变量增强/减弱和反方判断再展开。终稿不单列正式估值章节，不放目标价、目标市值、PE/PEG/SOTP 表，也不写买卖建议；PEG 估值因子、情景准入和模型消费规则由终稿通过后的 `peg_valuation_handoff` 承接，三表/FCF 驱动、PEG-ready 候选字段和 DCF-ready 候选字段由终稿通过后的 `dcf_financial_model_handoff` 承接，并由 Financial Modeling 产出 PEG-ready 与 DCF-ready 两个数据包。

终稿完成后必须按 `qa-gates.md` 执行终稿 QA，并按 `final-report.md` 运行 `scripts/final_report_gate.py`；未通过时不得向用户宣称终稿完成，必须补写后复跑。正式导出 PDF/HTML 前，必须运行 `$research-report-publication-editor` 的 publication hygiene gate。

## Output Discipline

最终回复用户时，除非用户要求只看终稿，否则要说明：

- 新生成了哪些中间文件。
- 哪些 agent / 阶段完成了哪些任务。
- 7 个核心私有研究模块、3 个横向护栏模块、中期进攻 QA、终审事实 QA、三表/FCF 建模 readiness、PEG 估值 readiness 和 post-report handoff stage 如何被覆盖，最好给出覆盖表。
- `final_report` 是否已经完成；若未完成，必须说明是用户明确要求暂停、闸门失败正在补写，还是遇到阻塞。不得在 `final_report.md` 缺失时说“研究完成”。
- 终稿文件路径。

最终回复前必须进行文件存在性检查：`<prefix>_final_report.md`、`<prefix>_report_outline.md` 和 `<prefix>_final_report_expansion_plan.md`。只要用户未明确要求停在中间阶段，任一缺失都必须继续补写，不应进入最终回复。

## References

- 数据路径与证据优先级：[references/data-path.md](references/data-path.md)
- 研究姿态与市场变量写法：[references/research-posture.md](references/research-posture.md)
- 多角色/subagent 编排：[references/agent-orchestration.md](references/agent-orchestration.md)
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
