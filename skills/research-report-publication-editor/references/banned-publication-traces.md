# 禁用痕迹与问题分类

## HIGH: 生产痕迹

不得出现在正式 PDF/HTML/Markdown 报告中：

```text
Markdown Report PDF
Generated through Markdown -> HTML/CSS -> PDF
For research discussion only
自然语言_选择合适的skill
启动subagent
所选 skill
所用 skill
subagent 中间产物
growth-stock-valuation
final_report_gate.py
闸门补写记录
final_report_expansion_plan
```

## MEDIUM: 内部流程语言

这些句子通常应改写为报告判断句：

```text
终稿必须...
终稿应...
终稿采用...
终稿不把...
正式报告必须写清楚...
最终执行纪律是...
本报告只回答...
调用某某 skill...
不能写成强投资判断...
不进正式主线...
```

## MEDIUM: 指令式语言

这类句子即使没有出现“终稿”，也像提示词或审稿规则，不像正式报告正文：

```text
必须拆成两面
必须看...
结论不能写成...
正式报告必须写清楚...
软件章节必须用...
利润桥不能用收入外推
最终执行纪律是...
```

推荐改成判断句：

```text
capex 对供应商和云厂商形成两条不同传导链。
该变量目前不足以支撑强判断。
软件环节的核心验证指标是收入质量，而非产品功能发布。
```

## LOW: 风格问题

不一定必须删除，但应控制频率：

```text
这张表说明...
普通投资者只要抓住...
最小跟踪清单可以压缩为...
谁在掏钱？
钱买什么？
AI 新闻多不多？
```
