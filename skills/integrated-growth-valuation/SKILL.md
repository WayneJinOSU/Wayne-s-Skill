---
name: integrated-growth-valuation
description: 成长股估值聚合器；只读取 growth-stock-valuation 的 PEG/动态 PE 输出和 skills/dcf-model 的 DCF 输出，将两个模型结果聚合成一份统一估值摘要、并列表、差异提示、关键假设、证伪点和跟踪清单。Use when 用户已经完成 PEG 与 DCF 两个独立估值 skill，希望把结果合并成一份正式估值汇总、统一 scorecard、当前市值隐含情景或模型差异摘要。
---

# Integrated Growth Valuation Aggregator

## Overview

本 skill 是估值聚合层，不是估值主控层，也不是第三个估值模型。

它只做一件事：把 `$growth-stock-valuation` 的 PEG 输出和 `/Users/a/.codex/skills/dcf-model` 的 DCF 输出聚合到一份统一可读的估值文件里。

核心分工：

```text
Financial Modeling -> 给两个模型提供利润锚和 UFCF 底稿
growth-stock-valuation -> PEG / 动态 PE 估值输出
skills/dcf-model -> DCF Excel、summary、validation 输出
Integrated Growth Valuation -> 聚合两个输出，形成统一阅读稿和 scorecard
```

关键原则：

- 不调用 Financial Modeling、`$growth-stock-valuation` 或 `dcf-model` 重新建模；如果上游产物缺失，只列缺口。
- 不自行硬算 PEG、DCF、目标市值、WACC、终值或每股价值。
- 不修改两个模型的结论；只并列展示、摘取共同点和差异点。
- 不机械平均 PEG 与 DCF，不创造一个“综合目标价”来覆盖两个模型原始输出。
- 可以输出统一摘要、模型并列表、差异提示、当前市值隐含情景、证伪点和跟踪清单。
- 默认不输出买卖评级、仓位建议或确定性收益承诺。

## When To Use

使用本 skill 处理：

- 已经存在 `$growth-stock-valuation` 输出和 `dcf-model` 输出，需要合并成一份统一估值汇总。
- 用户要求“把 PEG 和 DCF 两个 skill 的结果聚合在一起”。
- 需要统一列出 PEG 区间、DCF 区间、当前市值隐含、关键假设、证伪点和跟踪指标。
- 需要做发布前口径检查，避免买卖建议、净利润折现、DCF 校验 PEG 等错误表述。

不适合：

- PEG 或 DCF 上游模型尚未输出；应先运行对应 skill。
- 业务主线、利润桥和关键财务驱动完全缺失；应先做投研或 dcf_financial_model_handoff。
- 银行、保险、券商、地产、资源品周期股等不适合普通 UFCF/PEG 框架的标的；除非用户明确要求并调整框架。
- 用户只要快速行情点评；可用轻量市场跟踪或投研 skill。

## Required Inputs

优先读取当前任务目录：

```text
research_artifacts/<标的>/
  <标的>_peg_valuation_deepdive.md
  <标的>_peg_valuation_scorecard.md
  <标的>_dcf_summary.md
  <标的>_dcf_model.xlsx
  <标的>_dcf_validation.json
```

可选读取：

```text
<标的>_dcf_financial_model_handoff.md
<标的>_peg_valuation_handoff.md
<标的>_final_report.md
```

若 PEG 或 DCF 核心输出缺失，不能生成正式聚合结论；只输出缺口清单。

## Workflow

### Step 1: 检查上游输出

确认是否存在：

```text
<标的>_peg_valuation_deepdive.md
<标的>_peg_valuation_scorecard.md
<标的>_dcf_summary.md
<标的>_dcf_validation.json
```

缺任一核心文件时，只列缺口和下一步要运行的 skill。

### Step 2: 摘取 PEG 与 DCF 结论

从 PEG 输出摘取：

```text
中性/乐观目标市值
动态 PEG 与复合 PEG
当前市值隐含情景
年份切换条件
触发条件与证伪点
```

从 DCF 输出摘取：

```text
企业价值、股权价值、每股价值/目标市值
WACC、终值假设、UFCF 路径
敏感性区间
validation 状态和主要警告
现金流质量约束
```

### Step 3: 聚合成统一阅读稿

只做并表和摘要：

```text
PEG 输出了什么
DCF 输出了什么
二者差异在哪里
哪些条件会让两个模型结果收敛或继续分化
下一步跟踪哪些指标
```

差异提示可参考 [model_conflict_matrix.md](references/model_conflict_matrix.md)，但不得替两个模型重算结论。

报告结构见 [synthesis_output.md](references/synthesis_output.md)。

### Step 4: Gate

交付前运行：

```bash
python3 /Users/a/.codex/skills/integrated-growth-valuation/scripts/valuation_gate.py \
  --artifact-dir research_artifacts/<标的> \
  --target <标的>
```

闸门规则见 [gate_rules.md](references/gate_rules.md)。

## Output Files

写入当前任务目录下：

```text
research_artifacts/<标的>/
  <标的>_valuation_aggregate.md
  <标的>_valuation_scorecard.md
```

文件定位：

- `valuation_aggregate`：PEG 与 DCF 输出的统一阅读稿。
- `valuation_scorecard`：一页式并列表和关键差异摘要。

## Non-negotiables

1. 不自行计算 PEG 或 DCF。
2. 不调用上游模型补跑；缺文件就列缺口。
3. 不修改 `$growth-stock-valuation` 或 `dcf-model` 的估值结论。
4. 不机械平均 PEG 与 DCF，不创造覆盖上游模型的新目标价。
5. 不输出买卖建议、评级、仓位建议或确定性收益承诺。
6. 若 PEG 与 DCF 差异大，只做差异提示和跟踪清单。
7. DCF validation 未通过时，聚合报告必须把 DCF 标记为未通过校验。
8. 最终回复用户时说明聚合了哪些上游文件、哪些文件缺失、闸门是否通过。
