# Aggregation Output

## Valuation Aggregate

`<标的>_valuation_aggregate.md` 推荐结构：

```text
# <标的> 估值聚合

## 1. 聚合结论摘要
## 2. 使用的上游文件与数据日期
## 3. PEG 输出摘要
## 4. DCF 输出摘要
## 5. PEG 与 DCF 并列表
## 6. 差异提示
## 7. 当前市值隐含情景
## 8. 共同触发条件与证伪点
## 9. 后续跟踪清单
## 10. 数据缺口与校验状态
```

若做正式 DCF，另行输出：

```text
<标的>_dcf_model.xlsx
<标的>_dcf_summary.md
<标的>_dcf_validation.json
```

这些文件由 `/Users/a/.codex/skills/dcf-model` 生成或校验；`integrated-growth-valuation` 只读取 DCF 摘要、校验结果和关键输出，用于聚合展示。

`dcf_model.xlsx` 必须保留公式、WACC build-up、敏感性和 source comments；`dcf_summary.md` 展示 DCF 桥和 EV-to-equity 结果；`dcf_validation.json` 保存 validator 结果。

若做 Scenario DCF，另行输出：

```text
<标的>_dcf_assumption_ledger.md
<标的>_scenario_dcf_summary.md
<标的>_scenario_dcf_model.xlsx
<标的>_scenario_dcf_validation.json
```

聚合报告中的 DCF 标题必须写成 `Scenario DCF`，并摘录 assumption ledger 中的来源类型和置信度。可以并列展示情景股权价值区间，但不得称为 Formal DCF 或审计级内在价值。

若做 Reverse DCF，另行输出：

```text
<标的>_dcf_assumption_ledger.md
<标的>_reverse_dcf_summary.md
```

聚合报告中的 DCF 标题必须写成 `Reverse DCF` 或“当前市值隐含现金流检验”，并说明它是反推，不是预测。

若做正式 PEG，另行输出：

```text
<标的>_peg_valuation_deepdive.md
<标的>_peg_valuation_scorecard.md
```

这些文件由 `$growth-stock-valuation` 生成；`integrated-growth-valuation` 只读取 PEG 结论、目标市值区间、当前隐含情景、年份切换条件和证伪点。

## Scorecard

`<标的>_valuation_scorecard.md` 推荐结构：

| 维度 | 判断 |
| --- | --- |
| 主线阶段 | 预期型/半兑现/兑现型/高潮型/证伪型 |
| PEG 结论 |  |
| DCF 结论 |  |
| DCF 模式 | Formal / Scenario / Reverse |
| 差异提示 |  |
| 当前市值隐含 |  |
| 区间并列 |  |
| 上行触发 |  |
| 下修触发 |  |
| 最关键跟踪指标 |  |

## Tracking List

`valuation_aggregate` 或 `valuation_scorecard` 内可包含：

| 模型发现 | 需要跟踪的指标 | 频率 | 方向阈值 | 对估值影响 |
| --- | --- | --- | --- | --- |

至少覆盖：

```text
收入/订单
毛利率
费用率
Capex/D&A
存货/应收/合同负债
OCF/UFCF
一致预期变化
市场估值锚变化
```

## Conclusion Language

推荐表达：

```text
PEG 给出成长定价上沿/中枢，DCF 给出现金流内在价值约束。
两个模型结果并列展示；差异来自 A、B、C。
后续需要跟踪 X、Y、Z 以判断 PEG 区间和 DCF 区间是否收敛。
```

避免表达：

```text
建议买入/卖出
目标价明确对应确定收益
DCF 证明 PEG 合理
PEG 修正 DCF
综合目标价取 PEG 与 DCF 平均
弱证据已经足以支撑基准估值
```
