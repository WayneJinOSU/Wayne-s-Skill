# QA Gates

本文件承接中期结构 QA、终审事实 QA、市场变量覆盖 QA、券商风格交付稿 QA 和出版清理。QA 的目标是校准和补厚，不是削弱主线气势。

## Midterm Structure Review

`<标的>_midterm_structure_review.md` 在写正式报告提纲前执行，必须检查：

- 是否缺行业空间、周期位置、供需缺口、价格周期。
- 是否缺技术路线、产品代际矩阵、价值量、ASP、毛利率和价格与利润传导。
- 是否缺竞争格局、客户链、认证阶段、份额、替代风险。
- 是否缺原材料价格链、转嫁率、库存和现金流影响。
- 是否缺产能地图、瓶颈产能、高端产能、第二曲线和归母口径。
- 是否缺订单 -> 排产 -> 出货 -> 收入确认 -> 利润释放 -> 现金回收传导链。
- 是否缺可计算利润模型、敏感性、跟踪体系和证据边界；中期 QA 不检查正式 handoff 文件。
- 是否有章节只是摘要，没有数据表、正文推理、变量增强/减弱和验证指标。
- 是否把核心变量只留在证据台账或 QA，没有进入正文提纲。

中期结构 QA 必须给出“必须补写清单”。主控补完后才能写 `report_outline`。

## Skeptic Review

`<标的>_skeptic_review.md` 在正式报告前执行，必须集中寻找：

- 哪些进攻型变量最可能被证伪。
- 哪些地方把行业景气直接跳成公司壁垒。
- 哪些地方把扩产当订单、把订单当利润、把收入增长当利润平台上移。
- 哪些市场变量或利润输入可能误导普通投资人，例如把市场口径当公告事实、把并表子公司利润重复计算、把权益法收益和协同收益重复计算、把周期峰值利润当长期中枢。
- 最关键 3-5 个证伪点。

终审 QA 必须写成分歧框架：乐观派在押什么，悲观派在怀疑什么，哪个经营信号出现说明乐观派占优，哪个经营信号出现说明只是周期修复、补库涨价或普通放量。

## Market Variable Coverage QA

正式报告前必须在 `<标的>_report_outline.md` 或 `<标的>_skeptic_review.md` 保留市场变量覆盖表：

| 市场变量 | 中间文件是否覆盖 | 正式报告是否保留 | 若删除，原因 |
| --- | --- | --- | --- |

凡市场变量属于高重要口径，例如客户份额、产品代际、ASP、毛利率、订单排产、良率、核心客户认证、上游关键材料锁定等，`正式报告是否保留` 原则上必须为“保留”。只有当变量与公司相关性弱、已被反证、或与另一个正文变量合并表达时，才允许删除，并必须写明。

## Brokerage Report QA

按 [brokerage-report.md](brokerage-report.md) 写 `<prefix>_brokerage_report.md` 后，必须执行以下检查：

1. 是否包含投资摘要/核心结论、公司定位与业务拆分、行业变化与市场交易主线、分业务增长逻辑、盈利传导与利润桥、催化剂与跟踪指标、风险提示/关键假设。
2. 市场变量是否被保留并翻译成 `基准驱动 / 上行情景 / 质量折扣 / 风险变量 / 催化剂`，而不是被删掉或只留在内部 QA。
3. 是否包含“盈利预测变量与情景假设表”，并写明变量、当前判断、是否进入基准假设、上行情景条件、对盈利的影响、跟踪指标和风险处理。
4. 是否大幅减少“不是、不能、反证、证伪、降级、闸门、正式报告、正文必须”等审计式语言，把边界改成研究判断、基准/上行情景、盈利质量折扣或风险触发器。
5. 是否清除 `Fact-ID`、skill/subagent、gate、自述式写作流程、内部文件名，以及 `handoff/base driver/scenario driver/tracking-only/quality discount/UFCF guardrail/blocking gap/估值接力/接力处理/研报定位/本文的核心/变量权重` 等系统或模型接口语言。
6. 是否仍不写目标价、目标市值、买卖建议或正式 PE/PEG/DCF 估值结论。
7. 按 [brokerage-report.md](brokerage-report.md) 运行 `scripts/brokerage_report_gate.py`；失败时改写 `brokerage_report`，不得删除变量来凑通过。

## Publication Hygiene

参考 `$chassis-growth-agentic-research` 的调用方式：正式导出 PDF/HTML 前，或用户要求正式版、发布版、对外版时，必须运行 `$research-report-publication-editor` 的 publication hygiene gate，清除导出痕迹、skill/subagent/任务名/工具名、正式报告自述、提示词残留、内部审稿语言和过度教学化表达。若存在 HIGH 问题，不得声称正式版完成；若存在 MEDIUM 问题，应先改写为报告判断语言；LOW 问题按报告风格和用户偏好处理。

## Post-Report Handoff QA

Post-report handoff QA 在 `skeptic_review` 存在、`brokerage_report` 完成且 `scripts/brokerage_report_gate.py` PASS 之后执行；两个 handoff 都必须存在。

检查项：

- `<prefix>_dcf_financial_model_handoff.md` 和 `<prefix>_peg_valuation_handoff.md` 必须都存在，且不得早于 `<prefix>_brokerage_report.md`。
- 两个 handoff 文件必须写明 `handoff_status: brokerage_report_passed`、`source_brokerage_report`、source paths、`brokerage_report_gate_status` 和 generation time。
- `dcf_financial_model_handoff` 只检查 DCF 准入、UFCF guardrails 和阻断缺口；不得重建三表、填正式预测或输出 DCF 结论。
- `peg_valuation_handoff` 必须把正式报告后的研究变量翻译成 PEG 因子消费规则，并逐项说明如何影响 PEG 系数：提高、降低、封顶、仅允许乐观情景、阻止年份切换或暂不影响。
- 任一 handoff 写成目标价、目标市值、买卖建议、半份估值报告或正式 PEG/DCF 结论，必须重写。
