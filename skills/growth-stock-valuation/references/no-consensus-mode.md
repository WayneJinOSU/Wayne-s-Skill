# No-Consensus Mode

当一致预期经过 fallback 后仍为 `data_gap`，但 PEG-ready 自有利润锚、YoY/CAGR、市场口径和质量说明完整时读取。

## Trigger

进入 `no_consensus_mode` 的条件：

- AkShare 主预测接口不可用或无有效机构预测。
- AkShare 备用接口不可用或不能提供净利润/EPS/机构数。
- Wencai 分年查询仍无可用机构预测，或只有单家/无法回源预测。
- 自有正常/乐观利润锚、YoY、CAGR、现金流质量和市场快照完整。

若自有利润锚也不完整，进入 `preparation_only`，不得输出目标市值。

## Output Discipline

必须显著标注：

```text
无一致预期版自建情景估值
一致预期差 = N/A
不是市场一致预期差驱动的正式估值
```

可以回答：

- 当前市值需要多少利润/PE 支撑。
- 自有正常/乐观情景下的目标市值区间。
- 倍数上修、下修、触发和证伪条件。

不能回答：

- 相对一致预期上修/下修空间。
- 市场预期差。
- 机构预测变化方向。

## Tables

保留一致预期列，但写 `N/A` 或 `data_gap`：

| 年份 | 一致预期净利润 | 自有正常 | 自有乐观 | 模式处理 |
| --- | ---: | ---: | ---: | --- |
| 2026E | N/A |  |  | 无一致预期，自有情景锚 |
| 2027E | N/A |  |  | 无一致预期，自有情景锚 |
| 2028E | N/A |  |  | 仅作年份切换观察 |

额外输出当前市值反推：

| 市场给定 PE | 当前市值所需利润 | 与自有情景关系 |
| ---: | ---: | --- |
| 30x |  |  |
| 40x |  |  |
| 50x |  |  |
| 60x |  |  |

## Naming

输出文件使用：

```text
<标的>_no_consensus_peg_valuation_deepdive.md
<标的>_no_consensus_peg_valuation_scorecard.md
```
