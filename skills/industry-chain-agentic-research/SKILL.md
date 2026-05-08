---
name: industry-chain-agentic-research
description: 强约束 Agentic 行业产业链深度研究；真实 subagent 优先，分角色证据收集、模块手册、子环节拆分、数据表沉淀、章节草稿、反查反证、反方审查、报告汇总、主笔重构和完整行业深度报告，用于 A 股/港股/美股行业、赛道、产业链或细分环节正式研究，防止摘要化、只说好话、终稿过薄、模块拼接和普通投资人读不懂。
---

# Agentic 行业产业链研究

## Overview

本 skill 是行业产业链研究的独立主控，不是摘要模板。它负责先建立主线假设，再优先启动真实 subagent 分角色查证；若宿主不允许真实 subagent，则用阶段文件模拟同样流程。正式交付必须是完整行业深度报告，而不是投研摘要；最终报告必须由主控基于 `report_synthesis.md`、`editorial_thesis.md` 和章节草稿重写，不能拼接各角色摘要。

九模块是研究覆盖底线，不是终稿目录。终稿必须像主笔写出的研究报告：先给读者一条可验证的投资主线，再把子环节排序、利润传导、公司兑现、估值预期和反证嵌入同一条叙事。

默认读者不是已经深耕该行业的专家，而是“具备基本投资常识、但不熟悉本产业链细节的普通投资人”。正式报告必须先用人话讲清楚：

```text
谁在花钱？
钱买了什么？
哪些环节能把收入变成利润和现金流？
哪些环节只是订单或主题映射？
当前估值已经提前反映了什么？
```

专业术语和细表可以保留，但必须先有普通读者能跟上的逻辑桥。

核心判断链：

```text
需求增长 + 供给约束 + 价格机制 + 利润池留存
+ 财务兑现 + 估值预期 + 反面证据
```

正式研究必须回答：

```text
行业怎么赚钱？
产业链变量如何一层一层传导？
利润留在哪个环节，为什么能守住？
行业变量如何进入上市公司收入、利润、现金流和估值？
当前市场预期已经反映到哪一步？
哪些反面证据会证明判断错了？
```

## When To Use

适合：

- 行业、赛道、产业链或细分环节研究。
- 判断某行业是否值得配置，或某家公司所处环节是否有利润池和壁垒。
- 用户要求 subagent、agentic、多角色、多阶段、完整流程、反查或反证研究。

不适合：

- 只要一句话观点或宏观新闻摘要。
- 单公司财报点评；底盘型成长股优先用 `$chassis-growth-agentic-research`，供应链平台型公司优先用 `$supply-chain-agentic-research`。
- 用户只要求快速判断时，只能输出 preliminary draft，并明确未完成正式 agentic 流程。

## Non-Negotiables

正式研究必须满足：

1. **真实 subagent 优先。** 若当前环境、宿主规则和工具能力允许，必须启动真实 subagent；阶段文件模拟只是在无法启动真实 subagent 时的降级执行载体，不是省时选项。
2. **先中间产物，后终稿。** 必须生成 `question`、`subsegment_map`、`agent_briefs`、`evidence_index`、`data_tables`、`transmission_map`、各角色文件、`negative_check`、`skeptic_review`、`report_synthesis`、`editorial_thesis`、`report_outline`、`final_report_full`、`plain_investor_guide` 和 `executive_summary`。
3. **研究覆盖要全。** 关键模块执行前必须读取对应 `references/modules/*.md`；九模块必须覆盖，大行业必须拆 3-7 个子环节。
4. **角色输出要可用。** 正向角色输出证据卡、研究稿和可入正文的章节草稿；`data_tables.md` 承担完整数据沉淀，不能用角色小结替代。
5. **主笔重构是硬闸门。** `report_synthesis.md` 之后、`report_outline.md` 之前，主控必须写 `editorial_thesis.md`，明确第一屏答案、一句话总判断、最终排序、利润桥覆盖、正文/附录取舍和反拼接自检。
6. **强判断必须有完整传导链。** 强结论必须走通 `下游需求/capex -> 采购决策/BOM -> 技术路线/规格变化 -> 供给瓶颈/价格 -> 供应商份额/客户验证 -> 订单/交付/收入确认 -> 毛利率/费用/折旧 -> 应收/存货/现金流 -> 估值隐含情景`；走不通只能写成观察或降级判断。
7. **估值与市场预期不拆分。** 二者统一由 `valuation_expectation.md` 处理；市场预期是估值判断的入口。
8. **反查不是风险提示。** 没有 `negative_check.md` 的研究只能标记为 preliminary draft；反查和反方审查要求降级的结论，终稿必须降级。
9. **事实、口径和假设分层。** 区分官方/协会数据、公司公告、订单排产库存、结构化市场数据、券商/媒体口径、合理推断和情景假设；每个强判断都要写清 `证据 -> 推理 -> 反证/替代解释 -> 判断强度`。
10. **终稿按主线写，不按模块拼。** `final_report_full.md` 默认采用 6-10 个一级章节或等价结构，由 `editorial_thesis.md` 决定；正文表格克制，默认每个核心章节只放 0-1 张真正推动叙事的表。
11. **可读性是硬约束。** `final_report_full.md` 第一屏必须有“普通投资者导读”或等价段落，用非术语语言解释行业生意、资金流、利润留存、主要陷阱和读法；另写 `<prefix>_plain_investor_guide.md`，把完整报告压缩成普通投资者能读懂的逻辑链。
12. **判断依据必须展开。** 每个核心判断都必须写清 `事实证据 -> 产业机制 -> 传导链条 -> 财务映射 -> 反证/替代解释 -> 判断强度`。不能只给结论表、排序表或一句“证据支持”；必须解释为什么该证据足以推出该判断，以及为什么不能推出更强判断。
13. **不为篇幅牺牲逻辑。** 正式报告不设硬性篇幅上限；如果传导链、判断依据和反证需要展开，就完整展开。压缩版只能放在 `executive_summary.md` 或 `plain_investor_guide.md`，不能让 `final_report_full.md` 像摘要。
14. **正式报告不能过薄，也不能离散。** 若只输出摘要、只给结论清单、缺少关键表格、没有展开产业机制、没有最终排序、没有完整传导链、没有普通读者逻辑桥或呈现为模块拼贴，只能标记为 preliminary / executive summary，不能称为正式行业研究报告。

## Execution Policy

正式研究必须触发 8 个研究角色：

```text
产业链定义
需求/供给/价格
利润池/竞争格局
财务映射/重点公司
估值与预期
反查/反证
反方审查
报告汇总
```

执行顺序、文件结构、角色输出、冲突处理和无真实 subagent 时的阶段模拟方式见 [references/orchestration.md](references/orchestration.md)。主控执行时应优先读取该文件。

正式深度报告的交付标准、子环节拆分、数据表、章节密度和防过薄验收见 [references/full-report-contract.md](references/full-report-contract.md)。主控在写 `agent_briefs.md`、`report_synthesis.md`、`editorial_thesis.md`、`report_outline.md` 和终稿前必须读取该文件。

主笔重构不是第 9 个研究角色，也不能外包给单个正向 subagent。subagent 负责证据卡、机制拆解、章节素材和反证；主控负责在 `editorial_thesis.md` 中裁剪、排序、降级和重写终稿结构。

关键模块手册：

| 模块 | 手册 |
| --- | --- |
| 需求/供给/价格 | [references/modules/demand_supply_price.md](references/modules/demand_supply_price.md) |
| 利润池/竞争格局 | [references/modules/profit_pool_competition.md](references/modules/profit_pool_competition.md) |
| 财务映射/重点公司 | [references/modules/financial_mapping_companies.md](references/modules/financial_mapping_companies.md) |
| 估值与预期 | [references/modules/valuation_expectation.md](references/modules/valuation_expectation.md) |
| 反查/反证 | [references/modules/negative_check.md](references/modules/negative_check.md) |

## Acceptance Checklist

交付前必须自检：

- 是否优先尝试真实 subagent；若未启动，是否说明宿主不允许并采用阶段文件模拟。
- `agent_briefs.md` 是否记录每个 agent 的任务、数据源、输出文件、模块手册和禁区。
- 大行业是否先拆 3-7 个子环节，并逐个回答需求、供给、价格、利润池、重点公司和证伪指标。
- 是否生成 `data_tables.md`，并沉淀行业规模、需求、供给、价格/成本、利润池、公司矩阵、估值和跟踪指标。
- 是否生成 `transmission_map.md`，逐层写清下游需求如何传到产品规格、BOM、订单、收入、利润、现金流和估值。
- `evidence_index.md` 是否记录来源、口径、可靠性、适用模块和数据缺口。
- 关键模块 agent 是否读取并遵守对应模块手册。
- 每个角色文件是否包含证据、推理、反证、判断强度和数据缺口。
- 每个关键角色是否提供可进入正文的章节草稿，而不仅是研究备忘录。
- `negative_check.md` 是否逐条反查看多主线，而不是只写一般风险。
- `report_synthesis.md` 是否处理 agent 冲突、证据强弱、结论降级，并列出终稿必须展开的细节、必须保留的表格和每章证据。
- `editorial_thesis.md` 是否给出第一屏答案、一句话总判断、普通投资者逻辑桥、最终排序、利润桥覆盖、正文/附录取舍和反拼接自检。
- 强结论是否走通从下游需求/capex 到采购结构、技术路线、供应商份额、收入、利润、现金流和估值的完整传导链；走不通的内容是否被降级。
- 每个核心判断是否展开了判断依据，而不是只给结论清单或摘要式表格。
- `final_report_full.md` 开头是否用普通人语言解释“谁掏钱、钱买什么、谁留利润、哪里会断、估值反映什么”，而不是直接进入术语和表格。
- 是否生成 `<prefix>_plain_investor_guide.md`，并用较少术语讲清行业生意、最终排序、三到五个常见误区和后续跟踪指标。
- `final_report_full.md` 是否按主线重写，默认采用 6-10 个一级章节或等价结构，而不是按九模块、12 章或 agent 文件顺序拼接。
- `final_report_full.md` 是否像完整行业深度报告，解释“行业怎么赚钱、利润留在哪、为什么能守住、如何进财报、估值是否反映、如何证伪”，而不是薄摘要或离散材料合集。
- `executive_summary.md` 是否只作为摘要，不替代正式报告。
- 任一项缺失时，不能声称完成正式研究，只能标记为 preliminary draft。

## Output Discipline

最终回复用户时，除非用户只要求看终稿，否则说明：

- 真实 subagent 或阶段模拟的执行情况。
- 新生成的中间文件。
- 九个核心模块如何覆盖。
- `editorial_thesis.md` 如何把模块材料重构成终稿主线、排序和利润桥。
- 普通投资者导读和 `plain_investor_guide.md` 如何把专业报告翻译成可理解的资金流、利润流和风险点。
- 反查发现了哪些反面证据，哪些结论被降级。
- 完整报告和摘要路径。

## References

- 总框架：[references/framework.md](references/framework.md)
- Agentic 编排：[references/orchestration.md](references/orchestration.md)
- 数据路径：[references/data-path.md](references/data-path.md)
- 正式报告深度合同：[references/full-report-contract.md](references/full-report-contract.md)
- 模块手册：[references/modules/](references/modules/)
- 报告写作：[references/report-writing.md](references/report-writing.md)
