# Parallel PEG / Bottom-Up Branches

用于用户明确要求“算小账”“bottom-up”“分板块利润桥”并与 PEG 估值并列对照时。目标是防止估值分支和利润计算分支上下文互相污染。

## Contents

- Architecture
- Shared Upstream
- PEG Valuation Subagent
- Bottom-Up Profit Subagent
- Main Controller
- Re-Run Rules

## Architecture

```text
Shared Catalyst Precheck
        |
        |-- PEG Valuation Branch
        |   `-- independent PEG subagent
        |
        |-- Bottom-up Profit Branch
        |   `-- independent bottom-up subagent
        |
        `-- Main Controller
            `-- parallel comparison module only
```

## Shared Upstream

共同上游只有：

- `<标的>_catalyst_precheck.md`
- 公司公告/财报事实
- 结构化行情、市值、财务、分业务、产能、原材料数据

`catalyst_precheck` 必须包含：

| Catalyst | Valuation consumption | Profit consumption | 证伪条件 |
| --- | --- | --- | --- |
|  | 对 PEG 档位、年份切换、质量折价的影响 | 对收入、ASP、毛利率、产能、原材料、费用、现金流的影响 |  |

## PEG Valuation Subagent

输入：

- `catalyst_precheck`
- PEG-ready 所需市场快照、股本、市值、一致预期
- 自有正常/乐观利润锚来源
- `peg_valuation_handoff`（若存在）

输出：

```text
<标的>_peg_ready_package.md
<标的>_peg_valuation_deepdive.md
<标的>_peg_valuation_scorecard.md
```

禁止：

- 读取 `<标的>_bottom_up_profit_bridge_recheck.md` 作为估值输入。
- 因 bottom-up 结论自动调整利润锚、PEG 档位或目标市值。

## Bottom-Up Profit Subagent

输入：

- `catalyst_precheck`
- 财报、分业务收入、产能、原材料、费用、税率、现金流、营运资本资料

输出：

```text
<标的>_bottom_up_profit_bridge_recheck.md
```

必须覆盖：

- 2025A/最新季度经营底盘
- 分业务收入小账
- 毛利率与成本小账
- 费用、财务费用、税率、少数股东
- 2026E/2027E 经营情景利润桥
- 与 PEG 利润锚的并列对照
- 跟踪指标和证据边界

禁止：

- 输出目标市值、目标价、PEG、买卖建议或估值结论。
- 使用一致预期作为利润锚。
- 使用当前市值或目标市值倒推利润。
- 把特定客户、份额、订单、ASP 写成事实，除非公告或财报明确披露。
- 修改 PEG 主报告。

## Main Controller

主控只做：

- 检查两个分支是否使用同一份 catalyst precheck。
- 检查文件边界是否被破坏。
- 生成 `<标的>_peg_bottom_up_parallel_module.md`。

并列模块必须包含：

```text
模块定位
并列结论
互不影响规则
正确阅读方式
后续更新触发
```

并列模块不得改写 PEG 或 bottom-up 结论。

## Re-Run Rules

- 若用户要求“用小账结果重跑 PEG”，重新启动 PEG 分支，并在输出中说明新输入和重跑原因。
- 若用户要求“用 PEG 锚校准小账”，重新启动 bottom-up 分支，并标注这是估值锚校准版，不是纯经营小账。
- 若没有明确重跑要求，两个分支互不回写。
