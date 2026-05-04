---
name: industry-chain-agentic-research
description: 强约束 Agentic 行业产业链研究；真实 subagent 优先，分角色证据收集、模块手册、反查反证、反方审查、报告汇总和投资人写作，用于 A 股/港股/美股行业、赛道、产业链或细分环节正式研究，防止摘要化和只说好话。
---

# Agentic 行业产业链研究

## Overview

本 skill 是行业产业链研究的独立主控，不是摘要模板。它负责先建立主线假设，再优先启动真实 subagent 分角色查证；若宿主不允许真实 subagent，则用阶段文件模拟同样流程。最终报告必须由主控基于 `report_synthesis.md` 重写，不能拼接各角色摘要。

核心判断链：

```text
需求增长 + 供给约束 + 价格机制 + 利润池留存
+ 财务兑现 + 估值预期 + 反面证据
```

正式研究必须回答：

```text
行业怎么赚钱？
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
2. **先中间产物，后终稿。** 必须生成 `question`、`agent_briefs`、`evidence_index`、各角色文件、`negative_check`、`skeptic_review`、`report_synthesis`、`report_outline`、`final_report`。
3. **关键模块读手册。** 需求/供给/价格、利润池/竞争格局、财务映射、估值与预期、反查/反证执行前必须读取对应 `references/modules/*.md`。
4. **九模块覆盖。** 必须按 `framework.md` 的九个模块覆盖，不得因为角色合并或报告压缩而省略。
5. **估值与市场预期不拆分。** 二者统一由 `valuation_expectation.md` 处理；市场预期是估值判断的入口。
6. **反查不是风险提示。** 没有 `negative_check.md` 的研究只能标记为 preliminary draft。
7. **强判断必须有证据链。** 每个强判断都要写清楚 `证据 -> 推理 -> 反证/替代解释 -> 判断强度`。
8. **事实、口径和假设分层。** 区分官方/协会数据、公司公告、订单排产库存、结构化市场数据、券商/媒体口径、合理推断和情景假设。
9. **禁止跳步。** 不能把行业景气直接写成公司受益，不能把收入增长直接写成利润增长，不能把一般风险提示当成反查。

## Execution Policy

正式研究必须触发 8 个角色：

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
- `evidence_index.md` 是否记录来源、口径、可靠性、适用模块和数据缺口。
- 关键模块 agent 是否读取并遵守对应模块手册。
- 每个角色文件是否包含证据、推理、反证、判断强度和数据缺口。
- `negative_check.md` 是否逐条反查看多主线，而不是只写一般风险。
- `report_synthesis.md` 是否处理 agent 冲突、证据强弱和结论降级。
- `final_report.md` 是否解释“行业怎么赚钱、利润留在哪、为什么能守住、如何进财报、估值是否反映、如何证伪”。
- 任一项缺失时，不能声称完成正式研究，只能标记为 preliminary draft。

## Output Discipline

最终回复用户时，除非用户只要求看终稿，否则说明：

- 真实 subagent 或阶段模拟的执行情况。
- 新生成的中间文件。
- 九个核心模块如何覆盖。
- 反查发现了哪些反面证据，哪些结论被降级。
- 最终报告路径。

## References

- 总框架：[references/framework.md](references/framework.md)
- Agentic 编排：[references/orchestration.md](references/orchestration.md)
- 数据路径：[references/data-path.md](references/data-path.md)
- 模块手册：[references/modules/](references/modules/)
- 报告写作：[references/report-writing.md](references/report-writing.md)
