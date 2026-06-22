# PEG Workflow Reference

用于正式 PEG / 动态 PE 估值。只在用户要求目标市值、目标价、动态 PEG、复合 PEG、估值年份切换或 scorecard 时读取。

## 1. Output Mode

| 模式 | 触发条件 | 允许输出 |
| --- | --- | --- |
| `consensus_mode` | 一致预期可用，PEG-ready 自有正常/乐观利润锚完整 | 正式 PEG 估值、正常/乐观目标市值、一致预期差、当前市值隐含预期 |
| `no_consensus_mode` | 一致预期 fallback 后仍缺失，但自有利润锚完整 | 自建情景目标市值、当前市值反推、触发/证伪条件 |
| `preparation_only` | PEG-ready 关键字段缺失 | 缺口清单、准备清单；不得输出目标市值 |

## 2. PEG-Ready Fields

最低字段：

| 字段 | 用途 |
| --- | --- |
| `valuation_date` | 固定股价、市值、预测和一致预期日期 |
| `current_market_cap` / `current_price` / `shares_outstanding` | 计算 Forward PE、目标价和隐含预期 |
| `consensus_profit_2026E/2027E/2028E` | 市场对照，不作为主目标市值分母 |
| `own_normal_profit_2026E/2027E/2028E` | 正常目标市值利润锚 |
| `own_bull_profit_2026E/2027E/2028E` | 乐观目标市值利润锚 |
| `profit_yoy_2027E/2028E` | 动态 PEG 增速 |
| `profit_cagr_2025A_2027E` / `profit_cagr_2026E_2028E` | 复合 PEG 增速 |
| `non_recurring_items` / `minority_interest` / `investment_income` | 利润质量检查 |
| `cashflow_quality_note` | OCF、营运资本、利润含金量折价 |
| `source_notes` | 数据来源 |

`peg_valuation_handoff` 只能提供 PEG 档位、情景准入、质量折价和年份切换边界，不能替代 PEG-ready。

## 3. Core Formulas

动态 PEG：

```text
动态 PEG = Forward PE / 对应年度净利润增速
对应 PE = 动态 PEG * 对应年度净利润增速
目标市值 = 利润锚 * 对应 PE
```

复合 PEG：

```text
复合 PEG = Forward PE / 未来 2-3 年归母净利润 CAGR
对应 PE = 复合 PEG * CAGR
目标市值 = 利润锚 * 对应 PE
```

当前年份为 2026 年时：

- 主表利润锚先用 2027E。
- 正常目标市值 = `own_normal_profit_2027E * 对应 PE`。
- 乐观目标市值 = `own_bull_profit_2027E * 对应 PE`。
- 2028E 只能作为估值年份切换或远期上沿单独列示。

## 4. Workflow

1. 读取或生成 `catalyst_precheck`。
2. 确认行情、市值、股本、PE/PB 和一致预期来源。
3. 读取或生成 PEG-ready 包。
4. 建立一致预期 vs 自有正常 vs 自有乐观对照表。
5. 建立三视角：Auditor View、PM View、Catalyst View。
6. 输出 2027E 动态 PEG 主表。
7. 输出 2027E 一年远期复合 PEG 守门表。
8. 输出当前市值隐含预期。
9. 判断市场状态和 PEG 容忍度。
10. 输出正常/乐观目标市值。
11. 单独列示 2028E 年份切换条件。
12. 输出倍数上修、倍数下修、触发条件和证伪点。

## 5. PEG Discipline

- 正常 PEG 常用 1.0-1.2x；结构牛/产业主升浪可提高，但必须有 catalyst 支撑。
- 乐观 PEG 不能只因为板块热度上修，必须绑定财报、订单、毛利率、现金流、年份切换或产品代际证据。
- 超过 1.5x 的 PEG 必须标注为趋势/泡沫上沿，不作为基础估值中枢。
- TTM PEG 只能快速观察，不作为主结论。
- 一致预期行只能用于市场对照和隐含预期，不得导出正常/乐观目标市值。

## 6. 2028E Switch

若列示 2028E，必须回答：

```text
是否允许切换：
必要触发条件：
2028E 利润锚：
对应 PE/PEG：
目标市值上沿：
为什么不能/可以当作正常估值：
```

默认不能把 2028E 当正常主锚，除非 2027E 已经过守门，且新增证据足以证明市场可提前资本化远期利润。
