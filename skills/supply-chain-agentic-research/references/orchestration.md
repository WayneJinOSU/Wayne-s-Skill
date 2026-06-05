# Deprecated: Orchestration

本文件保留为旧引用兼容入口。正式编排规则已经迁移到 [agent-orchestration.md](agent-orchestration.md)；终稿提纲、扩写蓝图、复杂度分档和反摘要闸门已经迁移到 [final-report.md](final-report.md)。

执行供应链正式研究时，不要再以本文件作为主流程来源。主控必须读取：

- [agent-orchestration.md](agent-orchestration.md)
- [research-posture.md](research-posture.md)
- [handoffs.md](handoffs.md)
- [qa-gates.md](qa-gates.md)
- [final-report.md](final-report.md)

若旧任务仍引用本文件，按以下兼容规则处理：

```text
1. 先读取 agent-orchestration.md 获取 subagent / 文件化阶段分组。
2. 再读取 final-report.md 获取 report_outline、final_report_expansion_plan、final_report 和 final_report_gate.py 的终点契约。
3. 不得从中间研究文件直接跳到 final_report；必须先写扩写蓝图并运行闸门。
```
