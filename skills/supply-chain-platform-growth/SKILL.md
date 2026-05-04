---
name: supply-chain-platform-growth
description: "研究处在 AI 算力、数据中心、先进制造、新能源、机器人等大产业周期中的供应链平台型成长股，判断公司是否发生身份切换、订单出货放量、利润中枢上移和远期估值重估。Use when analyzing companies like 工业富联、AI服务器制造、高速PCB、液冷散热、电源、连接器、光模块供应链、先进封装设备/材料等，不适合银行、纯消费、纯资源周期或无收入利润底盘的概念股。"
---

# 供应链平台型成长股研究

## Overview

用于分析“不是最高技术定义者，但在大产业周期里承担关键制造、交付、材料、设备、连接、散热、电源或配套角色”的供应链平台型公司。

核心问题：

```text
这家公司是否从普通制造/代工/零部件身份，切换为大产业周期里的关键供应链交付平台？
订单和出货是否能推动利润中枢上移？
当前市值是否已经透支未来 2 到 3 年利润？
```

一句话方法：

```text
先判断产业周期，再判断供应链地位，再判断利润中枢是否上移，最后判断估值是否透支。
```

## Relationship To Other Growth Skills

把本 skill 当作独立主控 skill 使用。它和 `chassis-growth-research` 并列：

- `chassis-growth-research`：侧重旧业务底盘、第二成长曲线、平台复用、利润桥和远期估值，适合“旧业务托底 + 新业务二次成长”的制造业公司。
- `supply-chain-platform-growth`：侧重身份切换、产业周期、供应链地位、订单出货领先指标和利润年份切换，适合“产业周期爆发 + 关键交付平台”的公司。

## Workflow

正式研究报告必须覆盖 6 个核心模块，不能只挑部分模块。只有用户明确要求“快速判断”“简单看一下”“先粗筛”时，才允许使用轻量模式，并必须说明哪些模块尚未完整验证。

1. 形成主线假设：市场正在交易身份切换、订单放量、利润中枢上移、估值透支还是错杀修复。
2. 框架适用性分诊：判断公司是适用、部分适用，还是不适用供应链平台型框架。
3. 选择证据路径：按 [references/data-path.md](references/data-path.md) 调度公告、`$tushare`、`$wencai-query`、客户 capex、海关/出货和行业数据。
4. 调用子工作流：按 [references/subworkflows.md](references/subworkflows.md) 覆盖周期、地位、订单、承接、利润桥、远期估值。
5. 权重排序：判断最终报告最重要的 2 到 3 个模块，不要平均用力。
6. 论证链补强：每个主导结论写出“证据 -> 推理 -> 反证 -> 判断”。
7. 合成结论：回答公司是在讲故事、正在验证、正在兑现，还是已经充分定价。

## Required Sub-Skills

正式研究优先调用：

- `$supply-chain-cycle-capex`：产业周期、客户资本开支、产品平台迭代和周期持续性。
- `$supply-chain-position-moat`：供应链位置、客户认证、交付壁垒、可替代性和议价权。
- `$supply-chain-orders-shipments`：订单、排产、出货、收入确认、营运质量和现金流。
- `$growth-execution-signals`：扩产、客户、订单、量产、海外基地和研发投入。
- `$growth-profit-bridge`：旧平台利润、新周期新增利润、扩张成本和情景测算。
- `$growth-forward-valuation`：当前市值隐含的 2025-2028 年利润情景和估值透支。

按需调用：

- `$growth-base-business`：旧业务底盘对估值下限很重要时调用。
- `$growth-platform-reuse`：从旧产品切入新周期需要验证能力复用时调用。
- `$growth-second-curve`：新周期空间、价值量和天花板需要展开时调用。

## Output Format

输出时优先按下面结构：

1. 主结论：预期型、半兑现型、兑现型供应链平台成长，或不符合框架。
2. 主线假设：市场正在交易什么，以及最需要验证的 3 个问题。
3. 子工作流调度表：列出核心模块结论、证据和权重。
4. 核心论证：按重要性写 2 到 3 条“证据 -> 推理 -> 反证 -> 判断”的论证链。
5. 利润中枢与估值：说明利润平台是否上移、当前市值反映到哪一年。
6. 证伪点：最关键的 3 到 5 个，并说明跟踪指标。
7. 最终判断：机会、风险、适合资金类型、当前是错杀、合理还是透支。

## References

判断框架、适用范围、阶段分类和常见误判见 [references/framework.md](references/framework.md)。

主工作流、子 skill 调度、检查项和报告组装见 [references/subworkflows.md](references/subworkflows.md)。

数据路径、证据优先级和口径纪律见 [references/data-path.md](references/data-path.md)。
