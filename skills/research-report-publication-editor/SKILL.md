---
name: research-report-publication-editor
description: 投研报告出版审校与对外口径清理；用于正式 PDF/Markdown/HTML 报告导出前后，扫描并清除导出痕迹、skill/subagent/任务名/工具名、终稿自述、提示词残留、内部审稿语言和过度教学化表达；可只列问题，也可在不改变事实和结论的前提下润色为正式研报正文。
---

# 投研报告出版审校

## Purpose

本 skill 是研究报告的出版前审校层，不重新研究行业或公司，也不改变结论。它负责把已经完成的产业链、供应链、成长股、估值或金融报告，从“内部研究产物”清理成“可对外阅读的正式报告”。

核心目标：

```text
删除生产痕迹 + 清理流程语言 + 改写提示词口吻 + 保留证据边界 + 不改事实结论
```

核心转换原则：

```text
把写作指令转成研究判断。
```

不要把“进攻性”和“边界感”删掉；只清理像提示词、审稿规则或作者自我提醒的句式。判断标准是：如果主语是“终稿/报告/写法/章节/结论/执行纪律”，通常属于内部写作指令；如果主语是“经营逻辑/利润桥/证据边界/市场定价/变量传导”，通常可以改写成正式研究判断。

## When To Use

适合用户要求：

- 检查报告是否有不像正式报告的描述。
- 清理 PDF/Markdown/HTML 中的导出痕迹、skill、subagent、任务名或工具名。
- 把“终稿必须/不能写成/执行纪律”这类内部审稿语言改成报告判断句。
- 把“报告不能/正确写法是/章节必须用”这类写作指令转成研究判断。
- 导出正式 PDF 前做 publication hygiene gate。
- 对已有报告做 scan only 或 rewrite。

不适合：

- 重新做行业研究、估值或单公司深研。
- 删除证据边界、风险提示或判断强度。
- 为了显得更顺滑而新增未经验证的数据。

## Workflow

### 1. Scan Only

用户只说“找问题”“看看哪里不像报告”时，只扫描不改写：

```bash
python3 /Users/a/.codex/skills/research-report-publication-editor/scripts/publication_hygiene_gate.py \
  "/absolute/path/report.pdf"
```

输出按严重程度分组：

- `HIGH`: 导出痕迹、任务名、skill/subagent/工具名、内部文件名。
- `MEDIUM`: 终稿自述、提示词/审稿规则残留、内部流程语言。
- `LOW`: 过度教学化、口语化旁白、重复“这张表说明”等风格问题。

### 2. Rewrite

用户要求润色或清理时，先保留原文件，再生成清理版 Markdown。不要改事实、数据、表格结论和判断强度。优先做局部替换：

```text
终稿应把服务器放在“需求兑现层”
-> 服务器更适合被定位为需求兑现层，而非核心利润池。

不能写成强投资判断
-> 该变量目前只能作为观察线，尚不足以支撑强判断。

所用 skill：supply-chain-agentic-research
-> 删除。
```

完整规则见 [references/rewrite-patterns.md](references/rewrite-patterns.md)。

### 2.1 指令句转换纪律

禁止保留这类结构：

```text
终稿必须...
报告不能...
正确写法是...
软件章节必须用...
最终执行纪律是...
```

推荐改成：

```text
本报告判断...
证据边界是...
当前更适合定义为...
该变量属于...
若成立...若不成立...
```

少量“必须/不能/只能/应当”可以保留在真实证据边界中，例如“不能把未披露订单金额写成事实”。但同一页或同一小节中若反复出现，优先改成“尚不足以支撑”“更适合作为”“需要由...验证”“进入...情景”等研究语言。

### 2.2 强约束词用途

允许保留：

```text
不能把未披露订单金额写成事实。
合同负债不能等同于完整订单。
单季现金流改善不能直接外推为长期拐点。
毛利率修复必须由产品结构、材料费和费用率共同验证。
```

这些句子约束的是证据、变量、财务科目和利润传导，属于报告严谨性。

需要改写：

```text
报告不能写成强投资判断。
终稿必须拆清楚。
结论不能写成...
软件章节必须用...
最终执行纪律是...
```

这些句子约束的是写作过程、章节处理和审稿规则，属于内部指令残留。改写时保留原来的边界含义，但把主语换成研究对象、证据边界或变量传导。

### 3. Gate Before Export

正式研究 skill 导出 PDF/HTML 前，应先运行 hygiene gate。若存在 `HIGH` 问题，不得导出正式版；若存在 `MEDIUM` 问题，应先改写为报告判断语言；`LOW` 问题可按报告风格和用户偏好处理。

## Non-Negotiables

1. 不得改变事实、来源、数据、数值、判断强度和证据等级。
2. 不得把必要的风险提示删成乐观表达；只能把内部审稿语言改成正式报告语言。
3. 不得在对外报告中保留：
   - `Markdown Report PDF`
   - `Generated through Markdown -> HTML/CSS -> PDF`
   - `自然语言_选择合适的skill`
   - `所选 skill` / `所用 skill`
   - `subagent 中间产物`
   - `growth-stock-valuation` 等工具/skill 名
4. 不得把内部文件、agent、QA、gate、扩写蓝图、闸门补写记录写进正文或来源表。
5. 若用户只要求找问题，最终只列问题，不输出重写稿。

## Output

Scan only 输出：

```text
总体判断：
高优先级问题：
中优先级问题：
低优先级问题：
建议处理顺序：
```

Rewrite 输出：

```text
新文件路径：
删除了哪些生产痕迹：
改写了哪些内部流程语言：
保留了哪些证据边界：
仍需人工确认的问题：
```

## References

- 禁用痕迹与分类：[references/banned-publication-traces.md](references/banned-publication-traces.md)
- 改写模式：[references/rewrite-patterns.md](references/rewrite-patterns.md)
