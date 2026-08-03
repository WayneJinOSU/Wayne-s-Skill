# Deprecated: Orchestration

本文件保留为旧引用兼容入口。正式编排规则已经迁移到 [agent-orchestration.md](agent-orchestration.md)；报告提纲、券商研报结构、复杂度分档和风格 gate 已经迁移到 [brokerage-report.md](brokerage-report.md)。

执行供应链正式研究时，不要再以本文件作为主流程来源。主控必须读取：

- [agent-orchestration.md](agent-orchestration.md)
- [research-posture.md](research-posture.md)
- [handoffs.md](handoffs.md)
- [qa-gates.md](qa-gates.md)
- [brokerage-report.md](brokerage-report.md)

若旧任务仍引用本文件，按以下兼容规则处理：

```text
1. 先读取 agent-orchestration.md 获取 subagent / 文件化阶段分组。
2. 再读取 brokerage-report.md 获取 report_outline、brokerage_report 和 brokerage_report_gate.py 的正式报告契约。
3. 不得从中间研究文件直接跳到估值 handoff；必须先完成 brokerage_report 并运行 brokerage_report_gate.py。
4. `brokerage_report_gate.py` PASS 后，才允许生成 `dcf_financial_model_handoff` 与 `peg_valuation_handoff`。
```
