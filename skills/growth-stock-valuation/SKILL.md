---
name: growth-stock-valuation
description: 成长股 PEG/动态 PE 估值 skill；用于成长股、供应链平台股、产业链龙头的 PEG、动态 PE、复合 PEG、目标市值、目标价、一致预期差、当前市值隐含预期、估值年份切换和证伪点分析。目标市值默认使用自有正常/乐观利润锚，一致预期只作市场对照；本 skill 不做 DCF。若用户要求 bottom-up/算小账/分业务利润桥与 PEG 并列对照，使用共享 catalyst precheck、独立 PEG subagent、独立 bottom-up subagent 和并列模块，防止估值与利润计算互相污染。
---

# 成长股 PEG / 动态 PE 估值

## Core Scope

本 skill 只回答 PEG / 动态 PE 定价问题：

```text
当前市值交易到哪一年利润？
正常/乐观自有利润锚对应多少目标市值？
一致预期是市场对照还是目标锚？
是否允许 PEG 上修或估值年份切换？
哪些证据会触发或证伪？
```

不做 DCF、SOTP 主估值、保守/悲观目标价表，也不从市场一致预期直接生成正常/乐观目标市值。

## Progressive Disclosure

主文件只保留路由和硬红线。按任务需要读取 references：

| 场景 | 必读 reference | 何时读取 |
| --- | --- | --- |
| 正式 PEG / 动态 PE 估值 | `references/peg-workflow.md`、`references/output-templates.md` | 输出目标市值、目标价、动态 PEG 或 scorecard 前 |
| A 股一致预期缺失或接口异常 | `references/a-share-consensus-preflight.md`、`references/data-source-fallbacks.md` | 主一致预期源失败、字段缺失或数值异常时 |
| 无一致预期但自有利润锚完整 | `references/no-consensus-mode.md` | fallback 后仍无可用一致预期时 |
| 用户要求算小账 / bottom-up / 分业务利润桥并列对照 | `references/parallel-peg-bottom-up-branches.md` | 需要 PEG 与利润小账并列且防止上下文污染时 |

不要一次性读取所有 references。先判断任务模式，再读取对应文件。

## Non-Negotiables

1. 正式估值必须先有 `catalyst_precheck` 或近期 `integrated_update`。若没有，生成 `<标的>_catalyst_precheck.md`。
2. 正常目标市值使用 `own_normal_profit_*`；乐观目标市值使用 `own_bull_profit_*`。一致预期只用于市场对照、隐含预期和一致预期差。
3. 当前年份为 2026 年时，主估值年份默认 `2027E`。不得跳过 2027E 直接把 2028E 当正常/乐观主锚。
4. 正常/乐观两档足够。不要输出保守、悲观、下限或 downside 目标市值表；风险用证伪点表达。
5. 三视角必须并列：`Auditor View` 看财报和现金流底线，`PM View` 看 12-24 个月市场定价，`Catalyst View` 看催化剂是否允许 PEG 上修或年份切换。
6. 不得让审计口径成为唯一结论，也不得让市场一致预期直接覆盖自有利润锚。
7. 若启用 bottom-up 并列小账，PEG 分支和 bottom-up 分支只能共享 `catalyst_precheck`、事实文件和公开财务数据；默认不得读取或回写彼此结论。
8. 若用户明确要求或授权 subagent/并行分支，PEG 和 bottom-up 必须分别由独立 subagent 完成；主控只生成并列对照模块。

## Required Inputs

优先读取当前任务目录：

```text
research_artifacts/<标的>/
```

正式 PEG 估值优先输入：

```text
<标的>_catalyst_precheck.md 或 <标的>_integrated_update.md
<标的>_peg_ready_package.md
<标的>_peg_valuation_handoff.md（若存在）
```

若缺字段，再按片段读取：

```text
<标的>_facts_core.md（若存在，优先 Fact-ID）
<标的>_evidence_index.md
<标的>_profit_bridge.md 或 <标的>_financial_profit_bridge.md
<标的>_orders_shipments_quality.md
<标的>_skeptic_review.md
<标的>_final_report.md
```

第三层文件只允许 `rg` 定位后读相关片段；不要全文读取大型深研文件来“熟悉背景”。

## Catalyst Precheck

正式估值前必须生成或复用 catalyst precheck。最低结构：

```text
基准假设：
最近增量证据：
Catalyst log：
Stage scorecard：
红黄绿灯：
未来 1-3 个月 watchlist：
对 PEG 系数的影响：
对估值年份切换的影响：
必须锁回 Auditor/PM 基准的证伪条件：
```

若启用 bottom-up 并列小账，precheck 还必须区分：

| Catalyst | Valuation consumption | Profit consumption | 证伪条件 |
| --- | --- | --- | --- |
|  | 如何影响 PEG 档位、年份切换、质量折价 | 如何影响收入、ASP、毛利率、产能、原材料、费用、现金流 |  |

同一份 catalyst precheck 是共同上游；不是两个分支各自编一套催化剂。

## Formal PEG Branch

读取 `references/peg-workflow.md` 后执行。核心步骤：

1. 确认输出模式：`consensus_mode`、`no_consensus_mode` 或 `preparation_only`。
2. 取得最新股价、市值、股本、PE/PB 和未来 2-3 年一致预期。
3. 补齐或读取 PEG-ready 包。
4. 对比一致预期、自有正常、自有乐观利润锚。
5. 计算 2027E 动态 PEG、2027E 复合 PEG、当前市值隐含预期。
6. 只输出正常和乐观目标市值。
7. 单独列示 2028E 年份切换条件，不把它混入正常主估值。

若一致预期不可用，读取 `references/no-consensus-mode.md`。

## Optional Bottom-Up Parallel Branch

只有用户明确要求“算小账 / bottom-up / 分板块利润桥 / 与 PEG 并列对照”时启用，并读取 `references/parallel-peg-bottom-up-branches.md`。

硬边界：

- Bottom-up 分支使用同一份 `catalyst_precheck`，但只消费其中的 `Profit consumption`。
- Bottom-up 分支只输出 `<标的>_bottom_up_profit_bridge_recheck.md`。
- Bottom-up 分支不输出目标市值、目标价、PEG、买卖建议。
- Bottom-up 分支不使用一致预期或当前市值倒推利润。
- PEG 分支不读取 bottom-up 输出，除非用户明确要求“用小账结果重跑 PEG”。
- 主控只输出 `<标的>_peg_bottom_up_parallel_module.md`，不得合并成一个新估值结论。

## Output Files

正式 PEG 输出：

```text
research_artifacts/<标的>/
  <标的>_peg_ready_package.md
  <标的>_catalyst_precheck.md
  <标的>_peg_valuation_deepdive.md
  <标的>_peg_valuation_scorecard.md
```

无一致预期输出：

```text
research_artifacts/<标的>/
  <标的>_peg_ready_package.md
  <标的>_catalyst_precheck.md
  <标的>_no_consensus_peg_valuation_deepdive.md
  <标的>_no_consensus_peg_valuation_scorecard.md
```

可选并列小账输出：

```text
research_artifacts/<标的>/
  <标的>_bottom_up_profit_bridge_recheck.md
  <标的>_peg_bottom_up_parallel_module.md
```

不要覆盖已有 `<标的>_valuation_scorecard.md`。本 skill 的正式 scorecard 文件必须带 `peg_` 或 `no_consensus_peg_` 前缀。

## Final Response

最终回复必须说明：

- 使用了哪些前置文件和数据源。
- 输出模式是 `consensus_mode`、`no_consensus_mode` 还是 `preparation_only`。
- 正常/乐观目标市值和关键触发条件。
- 未能验证的数据缺口。
- 若启用 bottom-up 并列小账：说明 `catalyst_precheck` 是共同上游，PEG 与 bottom-up 由独立分支完成，主控只做并列对照，双方互不回写。
