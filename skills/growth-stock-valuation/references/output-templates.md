# Output Templates

用于正式产物命名和报告结构。普通估值任务只需读取本文件中的对应模式。

## Consensus Mode Files

```text
research_artifacts/<标的>/
  <标的>_peg_ready_package.md
  <标的>_catalyst_precheck.md
  <标的>_peg_valuation_deepdive.md
  <标的>_peg_valuation_scorecard.md
```

## No-Consensus Mode Files

```text
research_artifacts/<标的>/
  <标的>_peg_ready_package.md
  <标的>_catalyst_precheck.md
  <标的>_no_consensus_peg_valuation_deepdive.md
  <标的>_no_consensus_peg_valuation_scorecard.md
```

## Optional Bottom-Up Parallel Files

```text
research_artifacts/<标的>/
  <标的>_bottom_up_profit_bridge_recheck.md
  <标的>_peg_bottom_up_parallel_module.md
```

## Deepdive Structure

`peg_valuation_deepdive` 建议结构：

```text
输出模式
输入读取范围和估值闸门
当前市场快照
因子消费规则检查
一致预期和自有锚对照
Auditor / PM / Catalyst View
动态 PEG 估值
2027E 一年远期复合 PEG 守门表
当前市值隐含预期
市场环境和 PEG 容忍度
正常和乐观目标市值
2028E 估值年份切换情景
倍数上修和下修条件
关键证伪点
下一次需要跟踪的数据
来源
```

## Scorecard Structure

`peg_valuation_scorecard` 建议结构：

```text
核心结论
评分
Auditor / PM / Catalyst View
动态 PEG 与复合 PEG
当前市值隐含
从正常走向乐观的触发条件
证伪点
数据缺口
来源
```

## Final Target Table

只保留正常和乐观：

| 情景 | 利润锚 | PEG | 对应 PE | 目标市值 | 相对当前空间 | 触发条件 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 正常 |  |  |  |  |  |  |
| 乐观 |  |  |  |  |  |  |

## File Rules

- 不覆盖已有 `<标的>_valuation_scorecard.md`。
- 正式 PEG 输出使用 `peg_valuation_scorecard` 或 `no_consensus_peg_valuation_scorecard`。
- 并列小账文件不是 PEG 主报告输入；不得自动写入或修改 PEG 主文件。
