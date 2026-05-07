# Agentic 编排细则

## 总控职责

总控像投研项目经理，不是把各角色内容粘起来。总控负责：

- 建立主线假设和研究边界。
- 对大行业先拆 3-7 个子环节，建立 `subsegment_map.md`。
- 建立研究目录和 `agent_briefs.md`。
- 优先调度真实 subagent；无法启动时才用阶段文件模拟。
- 要求关键角色读取对应模块手册。
- 处理角色冲突、证据缺口和结论降级。
- 组织 `data_tables.md` 和章节草稿。
- 基于 `report_synthesis.md` 写 `editorial_thesis.md`，完成主笔重构、排序、利润桥和正文取舍。
- 基于 `editorial_thesis.md` 重写 `final_report_full.md`，并另写 `executive_summary.md`。

## 文件结构

```text
research_artifacts/<行业或公司>/
  <行业或公司>_question.md
  <行业或公司>_subsegment_map.md
  <行业或公司>_agent_briefs.md
  <行业或公司>_evidence_index.md
  <行业或公司>_data_tables.md
  <行业或公司>_industry_chain.md
  <行业或公司>_demand_supply_price.md
  <行业或公司>_profit_pool_competition.md
  <行业或公司>_financial_mapping_companies.md
  <行业或公司>_valuation_expectation.md
  <行业或公司>_negative_check.md
  <行业或公司>_skeptic_review.md
  <行业或公司>_report_synthesis.md
  <行业或公司>_editorial_thesis.md
  <行业或公司>_report_outline.md
  <行业或公司>_final_report_full.md
  <行业或公司>_executive_summary.md
  chapter_drafts/
    <行业或公司>_<章节>.md
  appendices/
    <行业或公司>_appendix_data.md
    <行业或公司>_company_matrix.md
    <行业或公司>_source_notes.md
    <行业或公司>_research_dossier.md   # 可选，资料卷，不替代正式终稿
```

同一轮研究内必须保持同一个文件名前缀。

如果研究对象是窄环节或小行业，`subsegment_map.md` 仍需生成，但可以说明“不拆分，理由是研究边界已经足够窄”。如果是大行业却没有拆 3-7 个子环节，不能进入正式研究。

## 研究角色与手册

正式研究必须触发 8 个研究角色。真实 subagent 是首选执行载体；若当前环境、宿主规则或工具能力不允许真实 subagent，才按“阶段文件模拟”执行。

所有研究角色至少包含：

```text
一句话贡献：
可支持的强判断：
必须降级或只能观察的判断：
已查证据：
数据口径与可靠性：
证据 -> 推理 -> 反证/替代解释 -> 判断强度：
数据缺口：
对主线的贡献：
可能推翻主线的证据：
终稿中应该放在哪一章：
可入正文的章节草稿：
```

正向研究角色必须输出“证据卡”，而不是各自写一篇小型终稿。每张证据卡至少包含：

```text
判断：
证据：
口径/来源可靠性：
传导链位置：
反证/替代解释：
判断强度：
适合放入终稿的位置：
```

| 文件或角色 | 输出文件 | 必读手册 | 核心职责 |
| --- | --- | --- | --- |
| Agent briefs | `agent_briefs.md` | 无 | 拆解主线、分配角色、规定数据源/禁区/反证方向 |
| Subsegment map | `subsegment_map.md` | `full-report-contract.md` | 大行业拆 3-7 个子环节，并规定每个子环节的需求、供给、价格、利润池、公司和证伪问题 |
| Evidence index | `evidence_index.md` | `data-path.md` | 汇总证据来源、口径、可靠性和数据缺口 |
| Data tables | `data_tables.md` | `full-report-contract.md` | 沉淀行业规模、需求、供给、价格/成本、利润池、公司矩阵、估值和跟踪指标 |
| 产业链与行业定义 | `industry_chain.md` | `framework.md` | 定义边界、行业类型、产业链位置和初步利润/风险集中环节 |
| 需求/供给/价格 | `demand_supply_price.md` | `modules/demand_supply_price.md` | 判断需求、供给、库存、价格和利润传导 |
| 利润池与竞争格局 | `profit_pool_competition.md` | `modules/profit_pool_competition.md` | 判断利润留在哪、壁垒是什么、利润池是否迁移 |
| 财务映射与重点公司 | `financial_mapping_companies.md` | `modules/financial_mapping_companies.md` | 把行业变量映射到收入、利润、现金流和公司分层 |
| 估值与预期 | `valuation_expectation.md` | `modules/valuation_expectation.md` | 估值与市场预期不拆分，反推当前价格隐含情景 |
| 反查/反证 | `negative_check.md` | `modules/negative_check.md` | 主动寻找推翻主线的事实，区分硬反证和一般风险 |
| 反方审查 | `skeptic_review.md` | 无 | 只挑错，检查逻辑跳步、估值误导、口径混用和读者理解断点 |
| 报告汇总 | `report_synthesis.md` | `full-report-contract.md` | 汇总冲突、证据强弱、降级结论、必须展开的细节、必须保留的表格和 full report 写作指令 |

关键模块角色的详细问题清单、禁止跳步、输出结构和判断强度标准以对应 `modules/*.md` 为准，不在本文件重复维护。

主笔重构不是新增第 9 个研究 subagent，而是主控在所有角色完成后的写作闸门。主控必须读取 `report-writing.md`，亲自把模块素材裁剪成 `editorial_thesis.md`，再写终稿。

## Subsegment Map

`subsegment_map.md` 在 `agent_briefs.md` 前完成。必须包含：

```text
是否属于大行业：
拆分原则：
3-7 个子环节：
每个子环节的卖点/买单方/需求/供给/价格/利润池/重点公司/反证：
哪些子环节进入正文重点展开：
哪些子环节仅放附录或观察池：
```

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
子环节拆分：
agent 分工表：
模块手册映射：
每个 agent 的必查数据：
每个 agent 的禁止越界事项：
反查重点：
章节草稿要求：
数据表要求：
最终交付清单：
```

最终交付清单必须包含 `data_tables.md`、`editorial_thesis.md`、`final_report_full.md` 和 `executive_summary.md`。
若需要保留大量背景资料、长表或公司细节，可增加 `research_dossier.md`，但它不能替代 `final_report_full.md`。

## Data Tables

`data_tables.md` 是正式报告厚度的骨架，必须按 [full-report-contract.md](full-report-contract.md) 建表。数据不足时不得省略表格，必须写明：

```text
证据不足：
缺少的数据：
当前只能做出的降级判断：
后续应跟踪的数据：
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

1. 主控先写 `question.md`、`subsegment_map.md`、`agent_briefs.md` 和初版 `evidence_index.md`。
2. 并行启动正向研究角色：产业链定义、需求/供给/价格、利润池/竞争格局、财务映射、估值与预期。每个正向角色必须输出证据卡、研究稿和可入正文的章节草稿，但不得把自己的输出写成完整终稿。
3. 主控把各角色新增证据汇入 `evidence_index.md`，并生成/更新 `data_tables.md`。
4. 正向研究文件和 `data_tables.md` 完成后，启动反查/反证角色。
5. 反查完成后，启动反方审查角色。
6. 全部中间文件完成后，启动或模拟报告汇总角色写 `report_synthesis.md`。
7. 主控读取 `report_synthesis.md`、章节草稿和 `data_tables.md`，亲自写 `editorial_thesis.md`。
8. 主控基于 `editorial_thesis.md` 写 `report_outline.md`、`final_report_full.md` 和 `executive_summary.md`。

如果用户明确要求 subagent、agentic、多角色或并行研究，视为已授权启动真实 subagent；若宿主仍不允许，必须说明并使用阶段文件模拟。

## 阶段文件模拟

无法启动真实 subagent 时，不得退回一次性写作。按以下顺序逐个文件模拟独立角色：

1. 写 `question.md`。
2. 写 `subsegment_map.md`。
3. 写 `agent_briefs.md`。
4. 写初版 `evidence_index.md`。
5. 写 `industry_chain.md`，并包含可入正文的章节草稿。
6. 读取前文和 `modules/demand_supply_price.md`，写 `demand_supply_price.md`，并包含可入正文的章节草稿。
7. 读取前文和 `modules/profit_pool_competition.md`，写 `profit_pool_competition.md`，并包含可入正文的章节草稿。
8. 读取前文和 `modules/financial_mapping_companies.md`，写 `financial_mapping_companies.md`，并包含可入正文的章节草稿。
9. 读取前文和 `modules/valuation_expectation.md`，写 `valuation_expectation.md`，并包含可入正文的章节草稿。
10. 把各正向阶段新增证据更新进 `evidence_index.md`，并写 `data_tables.md`。
11. 读取全部正向研究和 `modules/negative_check.md`，写 `negative_check.md`。
12. 读取全部研究和反查文件，写 `skeptic_review.md`。
13. 读取全部中间文件和 `full-report-contract.md`，写 `report_synthesis.md`。
14. 读取 `report_synthesis.md`、`data_tables.md`、章节草稿和 `report-writing.md`，写 `editorial_thesis.md`。
15. 读取 `editorial_thesis.md`、`report_synthesis.md`、`data_tables.md` 和章节草稿，写 `report_outline.md`、`final_report_full.md` 和 `executive_summary.md`。

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
可入正文的章节草稿：
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
最终排序：
利润桥覆盖表：
必须解释的人话概念：
终稿必须展开的 10-20 个细节：
必须保留的表格：
每章必须引用的证据：
不得压缩掉的产业机制：
正文 vs 附录分配：
证据卡到正文位置映射：
可能导致终稿离散的拼接风险：
正文结构：
不应写入强结论的内容：
覆盖表：
executive_summary 写作指令：
final_report_full 写作指令：
```

### 主笔重构

`editorial_thesis.md` 是从研究材料到正式终稿的硬闸门。必须包含：

```text
第一屏答案：
一句话总判断：
本文真正要证明的 3-5 件事：
终稿不按模块顺序拼接的理由：
最终排序：
- 强主线：
- 中强主线：
- 交易线：
- 验证线：
- 剔除线：
利润桥覆盖表：
- 子环节/公司：
- 需求或 capex：
- BOM/采购结构/价格：
- 份额或客户：
- 收入确认：
- 毛利率/费用/折旧：
- 应收/存货/现金流：
- 估值隐含情景：
- 证据缺口与降级：
正文必须保留的 5-10 个证据点：
正文只需点到、进入附录或 dossier 的内容：
章节顺序与每章要解决的问题：
每章只能保留的核心表格：
反查和反方观点嵌入位置：
反拼接自检：
```

如果 `editorial_thesis.md` 无法给出最终排序或利润桥覆盖，终稿只能标记为 preliminary draft。

### 报告提纲

`report_outline.md` 必须基于 `editorial_thesis.md` 和 `report_synthesis.md`，至少回答：

```text
读者第一眼需要先理解什么：
第一屏答案：
全文主线：
必须用人话解释的术语：
必须保留的表格：
被降级或不应写成强结论的内容：
最终报告 6-10 个一级章节或等价结构：
摘要报告结构：
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

终稿不是拼接中间稿。主控必须基于 `editorial_thesis.md`、`report_synthesis.md`、`data_tables.md` 和章节草稿重新排序：

- 先解释行业卖什么、谁买单。
- 再解释需求和供给如何影响价格。
- 再解释利润为什么留在某个环节。
- 再解释哪些公司能把行业变量兑现进财报。
- 再解释估值和预期已经反映到哪一步。
- 最后嵌入反查结论、反方观点和证伪指标。
- 另写 `executive_summary.md`，只做摘要，不替代 full report。

每个中间稿的“对主线的贡献”只能作为素材，不能原样堆进终稿。

以下任一情况出现，说明终稿仍是拼接稿，必须回到 `editorial_thesis.md` 重写：

- 章节顺序基本复制九模块、12 章模板或 agent 文件顺序，却没有解释这种顺序为什么最适合读者。
- 每章都用相同结构堆“定义、数据、公司、风险”，缺少递进。
- 表格数量很多，但没有回答“这改变了哪个投资判断”。
- 没有最终排序，读者不知道哪些子环节该重点看、哪些只是观察。
- 强结论没有从需求/capex 走到收入、利润、现金流和估值。
