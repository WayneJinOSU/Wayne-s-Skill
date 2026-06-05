# QA Gates

本文件承接 `SKILL.md` 的中期 QA、终审事实 QA、市场变量覆盖 QA、终稿 QA 和出版清理要求。QA 的目的不是削弱主线，而是让进攻型逻辑更完整、边界更清楚、证伪路径更可跟踪。

## Midterm Structure Review

中期进攻 QA 写入 `<标的简称或代码>_midterm_structure_review.md`，在写终稿提纲前执行：

- 检查是否缺市场重定价变量、旧业务底盘、第二曲线、行业经济性与蛋糕分配、TAM/SAM/SOM、公司份额、平台复用、竞争客户链、承接动作、利润斜率、跟踪体系和证据边界。
- 检查利润桥是否足以支撑终稿讨论利润中枢和利润斜率：至少说明收入、毛利率、费用、capex、营运资本、现金流、少数股东/投资收益和关键敏感变量如何影响主线。若缺失，必须补写利润桥或证据边界。
- 中期 QA 不检查正式 `dcf_financial_model_handoff` 或 `peg_valuation_handoff`；正式 handoff 字段完整性和 PEG 系数机制只在 post-report handoff QA 检查。
- 检查是否缺“进攻型主线”：市场到底在押什么、为什么不是旧业务修复/普通扩产/概念映射、客户份额/毛利率/产品放量若成立如何改变利润斜率、下一季什么信号会让逻辑升级。
- 检查每个核心模块是否都有“上行情景交付块”，且上行变量已经进入利润桥、跟踪体系和终稿提纲。
- 检查是否把行业空间直接写成公司利润、把客户线索直接写成订单、把扩产直接写成兑现。
- 检查高重要市场口径是否进入正文主线、利润桥和跟踪体系，而不是只留在证据台账或反方审查。
- 检查终稿提纲是否只有框架栏目、没有结论型标题和变量传导。
- 若发现缺口，必须列出“必须补写清单”；主控补完后才能写 `final_report`。

## Skeptic Review

终审事实 QA/反方审查写入 `<标的简称或代码>_skeptic_review.md`，在终稿前执行；它只校准边界，不负责削弱主线气势：

- 哪些结论证据不足。
- 哪些地方混用了 TAM/SAM/SOM，或把行业空间直接跳成了公司利润。
- 哪些地方把扩产当订单、把订单当利润、把收入增长当利润平台上移。
- 哪些市场变量或利润输入可能误导普通投资人。
- 哪些高重要变量虽然不能写成事实，但仍必须作为市场口径、情景假设或跟踪变量保留。
- 最关键 3-5 个证伪点。

## Market Variable Coverage QA

终稿前必须做市场变量覆盖 QA：

| 市场变量 | 中间文件是否覆盖 | 终稿是否保留 | 若删除，原因 |
| --- | --- | --- | --- |

凡高重要市场变量进入了证据台账、模块文件、利润桥或反方审查，原则上也要进入终稿正文。只有当变量与公司相关性弱、已被反证、或与另一个正文变量合并表达时，才允许删除，并必须写明。

## Final Report QA

终稿写作必须执行以下 QA：

```text
1. 搜索“后续关注、仍需验证、不能写成事实、证据不足、待验证”等词。
2. 若这些词出现在核心变量段落，必须改写成“变量增强/减弱时结论如何变化”。
3. 搜索“平台化、协同、国产替代、第二曲线、生态化”等抽象词。
4. 若这些词没有伴随收入、毛利率、费用率、客户、订单、现金流或复用链条解释，必须重写。
5. 搜索“估值、目标价、目标市值、PE、PEG、SOTP、隐含利润、赔率、定价”等词。
6. 若出现在 final_report 中形成估值结论，必须删除；若只是 PEG 估值因子、情景准入、年份切换或质量折价，可移至 post-report `peg_valuation_handoff` 的待承接清单；若是三表/FCF 驱动、PEG-ready 候选字段、DCF-ready 候选字段、WACC、UFCF 或 validation 驱动，可移至 post-report `dcf_financial_model_handoff` 的待承接清单，但不得形成目标价、目标市值、买卖建议或“当前贵不贵”。
7. 随机抽查 3 个核心章节：如果章节主要由表格和短结论组成，必须补写段落。
8. 搜索一级标题：若标题没有变量、机制或结论方向，必须重写为结论型标题。
9. 对照 final_report_expansion_plan 的章节素材映射表：若中间文件中的关键证据只在终稿中被一句话概括，必须恢复为完整论证。
10. 运行 scripts/final_report_gate.py。若失败，必须把失败项写入 <标的>_final_report_expansion_plan.md 的“闸门补写记录”，补写后复跑。最终回复用户时说明闸门是否通过。
```

## Publication Hygiene

正式导出 PDF/HTML 前，必须运行 `$research-report-publication-editor` 的 publication hygiene gate，清除导出痕迹、skill/subagent/工具名、终稿自述和提示词式内部审稿语言；若存在 HIGH 问题，不得声称正式版完成。

## Post-Report Handoff QA

正式 valuation handoff QA 只能在 `final_report` 完成、`skeptic_review` 存在且 `scripts/final_report_gate.py` PASS 之后执行。

检查项：

- `<prefix>_dcf_financial_model_handoff.md` 和 `<prefix>_peg_valuation_handoff.md` 必须同时存在，且生成时间不得早于 `<prefix>_final_report.md`。
- 两个文件都必须写明 `handoff_status: final_report_passed`、source paths、gate status 和 generation time。
- `dcf_financial_model_handoff` 必须把终稿后的研究变量翻译成 `$financial-modeling` 可消费的 PEG-ready 候选字段、DCF-ready/UFCF bridge、validation 要求和数据缺口。
- `peg_valuation_handoff` 必须把终稿后的研究变量翻译成 PEG 因子消费规则，并逐项说明如何影响 PEG 系数：提高、降低、封顶、仅允许乐观情景、阻止年份切换或暂不影响。
- 任一 handoff 写成目标价、目标市值、买卖建议、半份估值报告或正式 PEG/DCF 结论，必须重写。
