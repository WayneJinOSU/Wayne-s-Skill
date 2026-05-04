# Agentic 编排细则

## 总控职责

总控像投研项目经理，不是把各角色内容粘起来。总控负责：

- 建立主线假设和研究边界。
- 建立研究目录和 `agent_briefs.md`。
- 优先调度真实 subagent；无法启动时才用阶段文件模拟。
- 要求关键角色读取对应模块手册。
- 处理角色冲突、证据缺口和结论降级。
- 基于 `report_synthesis.md` 重写终稿。

## 文件结构

```text
research_artifacts/<行业或公司>/
  <行业或公司>_question.md
  <行业或公司>_agent_briefs.md
  <行业或公司>_evidence_index.md
  <行业或公司>_industry_chain.md
  <行业或公司>_demand_supply_price.md
  <行业或公司>_profit_pool_competition.md
  <行业或公司>_financial_mapping_companies.md
  <行业或公司>_valuation_expectation.md
  <行业或公司>_negative_check.md
  <行业或公司>_skeptic_review.md
  <行业或公司>_report_synthesis.md
  <行业或公司>_report_outline.md
  <行业或公司>_final_report.md
```

同一轮研究内必须保持同一个文件名前缀。

## 角色与手册

正式研究必须触发 8 个角色。真实 subagent 是首选执行载体；若当前环境、宿主规则或工具能力不允许真实 subagent，才按“阶段文件模拟”执行。

所有研究角色至少包含：

```text
已查证据：
数据口径与可靠性：
证据 -> 推理 -> 反证/替代解释 -> 判断强度：
数据缺口：
对主线的贡献：
可能推翻主线的证据：
终稿中应该放在哪一章：
```

| 文件或角色 | 输出文件 | 必读手册 | 核心职责 |
| --- | --- | --- | --- |
| Agent briefs | `agent_briefs.md` | 无 | 拆解主线、分配角色、规定数据源/禁区/反证方向 |
| Evidence index | `evidence_index.md` | `data-path.md` | 汇总证据来源、口径、可靠性和数据缺口 |
| 产业链与行业定义 | `industry_chain.md` | `framework.md` | 定义边界、行业类型、产业链位置和初步利润/风险集中环节 |
| 需求/供给/价格 | `demand_supply_price.md` | `modules/demand_supply_price.md` | 判断需求、供给、库存、价格和利润传导 |
| 利润池与竞争格局 | `profit_pool_competition.md` | `modules/profit_pool_competition.md` | 判断利润留在哪、壁垒是什么、利润池是否迁移 |
| 财务映射与重点公司 | `financial_mapping_companies.md` | `modules/financial_mapping_companies.md` | 把行业变量映射到收入、利润、现金流和公司分层 |
| 估值与预期 | `valuation_expectation.md` | `modules/valuation_expectation.md` | 估值与市场预期不拆分，反推当前价格隐含情景 |
| 反查/反证 | `negative_check.md` | `modules/negative_check.md` | 主动寻找推翻主线的事实，区分硬反证和一般风险 |
| 反方审查 | `skeptic_review.md` | 无 | 只挑错，检查逻辑跳步、估值误导、口径混用和读者理解断点 |
| 报告汇总 | `report_synthesis.md` | 无 | 汇总冲突、证据强弱、降级结论和终稿写作指令 |

关键模块角色的详细问题清单、禁止跳步、输出结构和判断强度标准以对应 `modules/*.md` 为准，不在本文件重复维护。

## Question

`question.md` 是研究起点，必须在派发 agent 前完成。

必须包含：

```text
研究对象边界：
行业类型分诊：
市场当前在交易什么：
需要验证的 3-5 个核心问题：
主线假设：
可能推翻主线的条件：
```

## Agent Briefs

`agent_briefs.md` 是正式研究闸门。没有它，不得启动正式研究。

必须包含：

```text
研究对象：
主线假设：
agent 分工表：
模块手册映射：
每个 agent 的必查数据：
每个 agent 的禁止越界事项：
反查重点：
最终交付清单：
```

## Evidence Index

`evidence_index.md` 是全局证据台账，不替代各 agent 的角色内证据表。它必须按 [data-path.md](data-path.md) 的优先级记录：

```text
来源：
链接或本地路径：
证据内容：
数据口径：
可靠性：强 / 中 / 弱
适用模块：
支持或反驳的判断：
数据缺口：
```

## 真实 Subagent 模式

当前环境、宿主规则和工具能力允许时，正式研究必须优先启动真实 subagent。

推荐调度：

1. 主控先写 `question.md`、`agent_briefs.md` 和初版 `evidence_index.md`。
2. 并行启动正向研究角色：产业链定义、需求/供给/价格、利润池/竞争格局、财务映射、估值与预期。
3. 主控把各角色新增证据汇入 `evidence_index.md`。
4. 正向研究文件完成后，启动反查/反证角色。
5. 反查完成后，启动反方审查角色。
6. 全部中间文件完成后，启动或模拟报告汇总角色写 `report_synthesis.md`。
7. 主控读取 `report_synthesis.md`、写 `report_outline.md` 和 `final_report.md`。

如果用户明确要求 subagent、agentic、多角色或并行研究，视为已授权启动真实 subagent；若宿主仍不允许，必须说明并使用阶段文件模拟。

## 阶段文件模拟

无法启动真实 subagent 时，不得退回一次性写作。按以下顺序逐个文件模拟独立角色：

1. 写 `question.md`。
2. 写 `agent_briefs.md`。
3. 写初版 `evidence_index.md`。
4. 写 `industry_chain.md`。
5. 读取前文和 `modules/demand_supply_price.md`，写 `demand_supply_price.md`。
6. 读取前文和 `modules/profit_pool_competition.md`，写 `profit_pool_competition.md`。
7. 读取前文和 `modules/financial_mapping_companies.md`，写 `financial_mapping_companies.md`。
8. 读取前文和 `modules/valuation_expectation.md`，写 `valuation_expectation.md`。
9. 把各正向阶段新增证据更新进 `evidence_index.md`。
10. 读取全部正向研究和 `modules/negative_check.md`，写 `negative_check.md`。
11. 读取全部研究和反查文件，写 `skeptic_review.md`。
12. 读取全部中间文件，写 `report_synthesis.md`。
13. 读取 `report_synthesis.md`，写 `report_outline.md` 和 `final_report.md`。

每一阶段都必须留下独立文件。信息不足时仍要生成文件，并写明已查证据、缺少数据、降级判断和下一步需要补什么。

## 非模块角色输出

### 产业链与行业定义

```text
行业定义：
行业类型：
产业链结构：
公司/重点环节位置：
利润与风险初判：
已查证据：
数据口径与可靠性：
证据 -> 推理 -> 反证/替代解释 -> 判断强度：
数据缺口：
对主线的贡献：
可能推翻主线的证据：
终稿中应该放在哪一章：
```

### 反方审查

```text
最大漏洞：
证据不足的结论：
行业景气到公司利润的跳步：
收入增长到利润增长的跳步：
可能误导的估值或行业口径：
替代解释：
读者理解断点：
反查模块是否充分：
必须补充或降级的判断：
最关键 3-7 个证伪点：
```

### 报告汇总

```text
全文主线：
最强证据：
最弱证据：
agent 结论冲突：
主控取舍：
必须降级的结论：
必须解释的人话概念：
正文结构：
不应写入强结论的内容：
覆盖表：
最终报告写作指令：
```

### 报告提纲

`report_outline.md` 必须基于 `report_synthesis.md`，至少回答：

```text
读者第一眼需要先理解什么：
全文主线：
必须用人话解释的术语：
必须保留的表格：
被降级或不应写成强结论的内容：
最终报告 7-10 个一级章节：
```

## 冲突处理

- 需求强但供给扩张更快：不能写行业景气，改写为“需求增长但利润被供给稀释”。
- 利润池在上游但公司处在中游：不能把行业利润直接映射到公司。
- 格局稳定但估值已高：结论写“好行业但预期已反映”。
- 财务映射显示收入增长但现金流恶化：不能写高质量增长。
- 反查找到客户砍单、价格下跌或库存累积：必须降级需求或利润池判断。
- 反查没有找到硬反证但有数据缺口：结论仍可成立，但判断强度不能写“强”。
- 技术路线存在替代风险：降低长期确定性，列为核心证伪点。
- 数据口径冲突：官方/公告优先，市场口径作为交易情绪或预期。

## 最终整合

终稿不是拼接中间稿。主控必须基于 `report_synthesis.md` 重新排序：

- 先解释行业卖什么、谁买单。
- 再解释需求和供给如何影响价格。
- 再解释利润为什么留在某个环节。
- 再解释哪些公司能把行业变量兑现进财报。
- 再解释估值和预期已经反映到哪一步。
- 最后嵌入反查结论、反方观点和证伪指标。

每个中间稿的“对主线的贡献”只能作为素材，不能原样堆进终稿。
