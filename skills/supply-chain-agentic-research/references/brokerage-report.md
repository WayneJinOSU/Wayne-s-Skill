# Brokerage Report Layer

本文件定义 `<prefix>_brokerage_report.md`：它是面向用户默认阅读的券商研报风格交付稿，也是本 workflow 的正式研究报告。事实追踪、审稿边界和内部完整性由 `facts_core`、分模块文件、`profit_bridge`、`tracking_dashboard`、`midterm_structure_review` 与 `skeptic_review` 承担；`brokerage_report` 负责把这些内容重构成清晰的投资逻辑、业务拆分、增长路径、盈利传导、催化剂和风险假设。

## Purpose

`brokerage_report` 不是删减版摘要，也不是 publication hygiene 的简单清理。它必须保留市场变量和后续盈利预测需要的判断，但要把变量翻译成券商研报正文能读懂的语言：

```text
市场变量 -> 业务定位 -> 盈利驱动 -> 基准/上行情景 -> 催化剂/跟踪指标 -> 风险处理
```

审稿语言、提示词语言、文件名、Fact-ID、subagent、gate、handoff 标签和“报告应当如何写”的自述留在内部文件中；对外正文只呈现研究判断。

## Required Structure

默认使用以下 H2 结构；标题可以改成更有结论密度的表达，但每类逻辑必须出现：

1. 投资摘要 / 核心结论
2. 公司定位与业务拆分
3. 行业变化与市场交易主线
4. 分业务增长逻辑
5. 盈利传导与利润桥
6. 盈利预测变量与情景假设
7. 催化剂与跟踪指标
8. 风险提示 / 关键假设

篇幅要求：

- `brokerage_report` 的最低正文厚度为 9500 个中文字符，以 `brokerage_report_gate.py` 的 `cjk_chars` 口径为准。
- `compact`、`standard`、`complex` profile 均不得低于 9500 个中文字符；`long-form` 不得低于 12000 个中文字符。
- 若用户明确要求极简版或只要摘要，必须说明这是用户指定的非正式压缩版；正式 workflow 的 `brokerage_report` gate 仍按上述门槛执行。
- 增厚必须来自订单质量、竞争格局、产品代际、利润桥、现金流验证、风险触发和跟踪体系的机制展开，不得用背景堆砌或重复事实凑字数。

建议保留的表格：

- 分业务收入、毛利率、战略定位和验证口径表。
- 市场交易主线和财务传导表。
- 分业务增长驱动表。
- 在手订单质量拆分表：按业务/产品等级/交付周期/毛利率线索/回款验证/风险触发拆分订单质量。
- 竞争格局、客户认证和份额口径表：按客户链层级、公司位置、关键竞品、认证阶段、份额或订单口径、ASP/毛利影响和证据等级拆分。
- 盈利传导/利润桥表。
- 盈利预测变量与情景假设表。
- 催化剂与跟踪指标表。

## Required Brokerage Logic Blocks

正式 `brokerage_report` 必须把“订单质量”和“竞争/客户链”写入正文，而不是只停留在中间产物、证据台账或风险提示。二者符合券商研报逻辑，因为它们分别回答“订单能否转成高质量利润”和“公司能否在行业机会中分到可持续份额”。

### 订单质量拆分

在“分业务增长逻辑”或“盈利传导与利润桥”中保留订单质量拆分表。不要只写订单金额；必须拆：

| 订单/业务 | 金额或规模 | 产品/项目质量 | 交付和收入确认 | 毛利率线索 | 回款/现金流验证 | 风险触发 |
| --- | --- | --- | --- | --- | --- | --- |

写法要求：

- 把订单从“金额”拆到“业务质量”：高端海缆、普通电网、低毛利新能源、AI 光互联等订单不能同等处理。
- 说明订单处在中标、合同、排产、交付、收入确认、回款中的哪一段。
- 订单的上行情景必须落回收入、ASP/价值量、毛利率、费用摊薄、应收/存货或经营现金流。
- 证据不足时写成情景变量或跟踪变量，不把订单金额直接写成利润。

### 竞争格局和客户认证链

在“公司定位与业务拆分”“行业变化与市场交易主线”或“分业务增长逻辑”中保留竞争/客户链对比表。不要只写“龙头”“客户优质”“格局好”；必须拆：

| 环节/产品 | 公司位置 | 关键竞品 | 客户/认证阶段 | 份额或订单口径 | ASP/毛利率影响 | 证据等级 | 验证指标 |
| --- | --- | --- | --- | --- | --- | --- | --- |

写法要求：

- 把“行业 beta”与“公司 alpha”分开：行业高景气只解释需求，公司份额、认证、交付和良率才解释公司利润。
- 竞品和份额资料若来自市场或券商口径，必须标明为市场口径或情景假设；不要伪装成公告事实。
- 客户链必须服务于盈利传导：客户认证、双供/多供、替代周期和客户粘性如何影响 ASP、毛利率、订单稳定性和现金流。
- 对普通投资人解释公司在供应链哪一层、与谁竞争、凭什么分到订单。

## Variable Preservation

券商风格不等于删除变量。对市场正在交易但证据尚未完全闭环的内容，必须转换为以下对外表达之一：

| 变量定位 | 对外正文写法 | 后续模型含义 |
| --- | --- | --- |
| 基准假设 | 已有财报或公告支撑，可纳入基准盈利假设 | handoff 中再标注为基准驱动 |
| 上行情景 | 能显著打开利润斜率，但订单、客户或毛利率仍待验证 | handoff 中再标注为情景驱动 |
| 盈利质量折扣 | 收入增长、并购、投资收益、少数股东或现金流影响利润质量 | handoff 中再标注为质量折扣 |
| 风险触发器 | 若恶化会使主线降级或利润桥下修 | handoff 中再标注为下修或阻断条件 |
| 催化剂 | 未来 4-8 个季度可能改变市场预期的经营信号 | handoff 中再标注为跟踪触发器 |

必须包含“盈利预测变量与情景假设表”，至少包含以下列：

| 变量 | 当前判断 | 是否进入基准假设 | 上行情景条件 | 对盈利的影响 | 跟踪指标 | 风险处理 |
| --- | --- | --- | --- | --- | --- | --- |

对外正文禁止写 `handoff处理`、`base driver`、`scenario driver`、`tracking-only`、`quality discount`、`UFCF guardrail`、`blocking gap` 等模型接口标签。这些标签只写入 `<prefix>_dcf_financial_model_handoff.md` 和 `<prefix>_peg_valuation_handoff.md`。不要在 `brokerage_report` 中给目标价、目标市值、买卖建议或正式 PE/PEG/DCF 结论。

## Style Rules

- 第一屏先讲投资摘要和核心结论，不先讲流程、证据边界或内部 QA。
- 每章先给判断，再给数据，再解释传导，最后放跟踪或风险。不要用“不是/不能/反证/降级”主导段落。
- 审计式表达要转成研究语言：
  - “不能写成订单” -> “当前仅进入上行情景，基准假设等待订单或收入确认”。
  - “反证变量” -> “对上行斜率形成约束”。
  - “降级路径” -> “若指标未兑现，主线回到周期修复或局部放量”。
  - “证伪指标” -> “跟踪指标/风险触发器”。
- 不在正文使用 `Fact-ID`。可写“公司 2025 年报显示”“2025H1 投关记录披露”“评级报告提示”等来源描述。内部追踪仍以 `facts_core` 和分模块文件为准。
- 避免把风险提示写成整篇报告的主语。风险和约束要服务于盈利传导、情景准入和跟踪体系。
- 变量、利润桥和催化剂要连起来：一个变量若进入报告，必须说明它影响收入、ASP/价值量、毛利率、费用、少数股东、投资收益、现金流或资本开支中的哪一项。
- 保持券商研报语气：判断明确、逻辑链完整、表格服务正文、风险在末尾集中收束。

## Style Normalization Pass

写完初稿后，必须做一次券商口吻改写。目标是删除系统语言，但保留变量：

| 不像券商的表达 | 券商正文表达 |
| --- | --- |
| 本文的核心不是把所有新业务同时上调为确定利润 | 我们认为，公司当前应按三层盈利框架拆分 |
| 后续估值接力的输入方式 | 盈利预测处理上 |
| 变量权重 | 对盈利预测的影响权重 |
| 变量到估值接力映射 | 盈利预测变量与情景假设 |
| handoff处理为 base driver | 可纳入基准盈利假设 |
| handoff处理为 scenario driver | 仅进入上行情景 |
| handoff处理为 quality discount | 应对该项收入贡献给予盈利质量折扣 |
| blocking gap / UFCF guardrail | 暂不支持进入基准现金流假设 |
| 这张表直接影响 DCF | 该表用于明确盈利预测的变量边界 |
| 报告定位 / 研报定位 | 业务定位 / 盈利定位 |

`brokerage_report` 不允许出现以下词或短语：`handoff`、`base driver`、`scenario driver`、`tracking-only`、`quality discount`、`UFCF guardrail`、`blocking gap`、`估值接力`、`接力处理`、`研报定位`、`本文的核心`、`变量权重`、`这张表直接影响 DCF`。

## Handoff Discipline

`brokerage_report_gate.py` PASS 后，才生成 post-report handoff。估值接力优先读取 `brokerage_report`，再读取 `skeptic_review`、`profit_bridge`、`tracking_dashboard` 和 `facts_core` 的必要片段。handoff 的 source paths 必须包含 `source_brokerage_report`，`handoff_status` 使用 `brokerage_report_passed`。

若 handoff 早于 `brokerage_report`，视为 stale，必须重写。下游估值不应消费旧的 handoff。

## Gate

写完 `<prefix>_brokerage_report.md` 后运行：

```bash
python3 /Users/a/.codex/skills/supply-chain-agentic-research/scripts/brokerage_report_gate.py \
  --profile auto \
  --market-variables-file "/absolute/path/research_artifacts/<prefix>/<prefix>_market_variables_map.md" \
  "/absolute/path/research_artifacts/<prefix>/<prefix>_brokerage_report.md"
```

闸门检查结构、表格、变量保留、盈利预测变量与情景假设、系统/模型接口语言、审计式否定语言密度、Fact-ID 泄漏、目标价/评级/正式估值误写和 publication hygiene。失败时改写 `brokerage_report`，不要削掉变量来凑通过。
