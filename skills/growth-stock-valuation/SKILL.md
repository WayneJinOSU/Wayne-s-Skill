---
name: growth-stock-valuation
description: 成长股专用 PEG/动态 PE 深度估值与定价判断；基于前置深研、利润桥和证据台账，以自有正常/乐观利润锚、动态 PEG、复合 PEG、一致预期差、隐含利润和牛市/产业主升浪估值容忍度为核心，只输出正常估值与乐观估值、触发条件和证伪点；一致预期用于市场对照和隐含预期反推，不默认作为目标市值利润锚；当一致预期缺失但 PEG-ready 自有利润锚完整时，可降级进入 no_consensus_mode，输出明确标注的自建情景估值和当前市值反推。本 skill 只做 PEG/动态 PE，不扩展到其他估值方法。Use when 用户要求对成长股、供应链平台股、底盘型成长股或产业链龙头做 PEG/动态 PE 估值、目标市值、PEG、一致预期差、估值透支、赔率、牛市估值上沿或估值锚切换分析。
---

# 成长股 PEG / 动态 PE 深度估值

## Overview

本 skill 专门回答 PEG/动态 PE 口径下的定价问题：

```text
主线逻辑成立以后，当前价格还值不值得买？
在产业主升浪、牛市或 AI 动能加持下，市场能给多少 PEG？
当前市值已经定价到哪一年利润，后面靠利润上修、PE 上修还是估值年份切换？
```

它不是从零做业务深研。优先接在 `$supply-chain-agentic-research`、`$chassis-growth-agentic-research`、`$industry-chain-agentic-research` 或已有研究产物之后使用，读取前置研究里的产业周期、公司卡位、订单出货、利润桥和反方审查，再单独做 PEG/动态 PE 估值判断。

Token discipline:

- 不降低估值质量：动态 PEG、复合 PEG、隐含预期、年份切换、触发条件和证伪点仍必须完整计算。
- 估值输入以 `<标的>_peg_ready_package.md` 为主数据源；若缺失，由本 skill 基于一致预期、facts_core、profit_bridge/handoff 生成或补齐，不得为 PEG 目的调用 `$financial-modeling`。
- 正式 PEG 估值前必须主动执行一次 `$equity-catalyst-tracker` 前置检查，或在无法嵌套调用 skill 时按其核心结构生成 `<标的>_catalyst_precheck.md`；该检查只服务 PEG/年份切换，不替代完整催化剂跟踪报告。
- 前置深研大文件默认不全文读取。`final_report`、`profit_bridge`、`skeptic_review` 和 `evidence_index` 只在 PEG-ready 或 handoff 缺字段、口径冲突或需要解释估值因子时按片段读取。
- 若研究目录存在 `<标的>_facts_core.md`，事实优先引用 `Fact-ID`；不要重复复制财报长表、公告原文、券商长段或前置报告大段。
- 最新行情、市值、股本和一致预期默认通过 skill/API 接口自动取得；只有接口失败、权限不可访问、字段缺失或明显异常时才 fallback 到第二个 skill/API 接口。
- 目标市值默认使用 PEG-ready 自有正常/乐观利润锚作为分母；一致预期只用于市场对照、一致预期差和当前市值隐含反推。禁止因为一致预期可用就直接用一致预期利润给正常/乐观目标市值，除非用户明确要求“按一致预期反推”，且必须标注为 `consensus-implied reference`，不得作为主结论。
- 一致预期缺失时，不要把估值任务全部阻断；若 PEG-ready 自有正常/乐观利润锚、YoY/CAGR 和现金流质量字段完整，切换到 `no_consensus_mode`，输出明确降级的自建情景估值和当前市值反推。
- SOTP、同行估值、新闻/研报列表只做必要摘要；不得为了背景完整而读入宽表、长 CSV 或完整研报清单。
- 本 skill 只做 PEG/动态 PE；若用户要求其他估值方法，只在最终回复中说明“本次输出范围为 PEG/动态 PE”。

核心判断不是简单看 PE 高低，而是：

```text
一致预期是否仍有上修空间
+ 动态 PEG 是否能解释当前/目标 PE
+ 复合 PEG 是否能穿透单年高增速
+ 牛市/产业主升浪是否允许更高 PEG
+ 下一组业绩或订单证据是否能触发估值年份切换
```

## When to use

适合用户要求：

- 判断成长股当前估值是否高估、合理、低估或仍有重估空间。
- 对比市场一致预期和自己的利润桥，找 EPS 上修空间。
- 使用动态 PEG、复合 PEG、隐含利润反推、目标市值或赔率分析。
- 判断牛市、产业主升浪或强动能趋势下，高 PE 是否仍可接受。
- 在已有深研基础上做估值接力，而不是重新研究业务。

若用户要求的不止 PEG，本 skill 仍只完成 PEG/动态 PE 部分；不要在本 skill 内扩展到其他估值方法。

不适合：

- 用户只需要快速行情观点。
- 没有收入、利润、订单、产能或财务基础的纯概念题材。
- 业务主线完全不清楚的标的；这种情况应先做完整深研或分诊。

## Required Inputs

优先读取当前任务目录下 `research_artifacts/<股票代码或公司简称>/` 的前置产物。按三层读取，不要把全部前置研究文件一次性读入上下文。

第一层：正式估值必读输入

```text
<标的>_question.md
<标的>_catalyst_precheck.md（若本次生成）或 <标的>_integrated_update.md（若已有近期 catalyst tracker 输出）
<标的>_peg_ready_package.md
<标的>_peg_valuation_handoff.md
```

第二层：事实和质量约束优先摘要读取

```text
<标的>_facts_core.md（若存在，优先用 Fact-ID）
```

第三层：仅在缺口或冲突时按片段读取

```text
<标的>_evidence_index.md
<标的>_profit_bridge.md 或 <标的>_financial_profit_bridge.md
<标的>_orders_shipments_quality.md
<标的>_skeptic_review.md
<标的>_final_report.md
```

第三层文件的使用原则：先用 `rg` 定位关键词、Fact-ID、年份、利润锚、订单、毛利率、现金流、证伪点或年份切换触发条件，再读取附近片段；不得全文读入以“熟悉背景”。若文件不存在，也只补齐估值所需字段，不重做业务深研。

正式估值闸门：

- 若只有 `<标的>_peg_valuation_handoff.md`，但没有 `<标的>_peg_ready_package.md`，本 skill 必须先尝试生成 PEG-ready 包；若一致预期、利润锚、YoY/CAGR、市场口径或质量说明仍缺关键字段，才输出“估值准备清单/缺口清单”。
- `<标的>_peg_valuation_handoff.md` 中出现的利润锚只能视为投研候选锚或情景边界，不能视为已完成口径统一、YoY/CAGR 校验和现金流质量校验的 PEG-ready 数据包。
- `<标的>_financial_model_output.md`、三表模型或其他估值文件不得替代 PEG-ready 包；它们只能作为现金流质量、营运资本或利润口径交叉检查材料。

必须额外获取并注明日期和来源：

- 最新股价、总市值、股本、TTM PE、静态 PE、PB。
- 市场一致预期：至少覆盖未来两年；能取得时覆盖第三年。
- A 股标的一致预期缺失或接口报错时，必须先读取 `references/a-share-consensus-preflight.md` 并完成硬性预检；不得因单一接口失败直接进入 `no_consensus_mode`。
- PEG-ready 数据包：由本 skill 读取或生成，包含市场一致预期、必要的自有情景/质量校验锚、YoY、2-3 年 CAGR、股本/市值、质量说明。不得让 `peg_valuation_handoff`、`financial-modeling` 或三表模型代替 PEG-ready 包。
- 产业阶段和市场状态：震荡市、结构牛、全面牛、产业主升浪、高潮期。
- 若存在 `<标的>_peg_valuation_handoff.md`，优先读取其中的 PEG 路径、核心因子接口、情景准入、年份切换和质量折价规则；若缺失或明显过期，不阻断估值，但必须在输出中说明 handoff 缺口并降低 PEG 档位置信度。`peg_valuation_handoff` 不是利润预测表，不得要求其提供自有利润锚、目标市值或最终倍数结论。

Catalyst 前置检查：

- 在生成 `<标的>_peg_valuation_deepdive.md` / `<标的>_peg_valuation_scorecard.md` 前，必须先显式使用 `$equity-catalyst-tracker`，聚焦最近公告、订单、财报、股价异动、产业新闻、客户/同行信号和未来 1-3 个月关键催化。
- 若当前环境无法真正嵌套调用 skill，必须按 `equity-catalyst-tracker` 的 Formal Tracker 核心结构生成或刷新 `research_artifacts/<标的>/<标的>_catalyst_precheck.md`；若已有同日或明确近期的 `<标的>_integrated_update.md`，可复用但需在估值报告中说明日期和有效性。
- `catalyst_precheck` 至少包含：baseline、catalyst log、stage scorecard、watchlist、红黄绿灯、关键证伪条件、能否支持 PEG 系数上修、能否支持估值年份切到更远期。
- 前置催化检查不得把未验证变量直接资本化为正常情景；只能通过明确触发条件进入乐观情景、年份切换情景或 PEG 上修条件。

结构化数据读取规则：

- 若 `<标的>_peg_ready_package.md` 已包含 `valuation_date`、`current_market_cap`、`current_price`、`shares_outstanding` 和一致预期字段，默认沿用该包，不再重复拉行情和一致预期。
- 若需要刷新行情，只取一个最新市场快照源；把刷新日期写入输出，避免同时拉多套行情表。
- 若需要补一致预期，只取一个一致预期来源并抽取未来 2-3 年利润、EPS、机构数和近 1-3 个月变化；不要读取完整研报列表。
- 若 skill/API 数据源失败、权限不可访问、关键字段缺失或数值明显异常，才记录 fallback 原因并换到下一个接口。禁止用非接口页面、手工网页、公开搜索或人工摘研报替代接口数据。

Skill/API 数据源阶梯：

| 数据需求 | 主接口 | 第一备用接口 | 第二备用接口 | 纪律 |
| --- | --- | --- | --- | --- |
| 最新股价、市值、股本、PE/PB | PEG-ready 包内市场字段 | `$akshare` A 股行情/历史行情接口 | `$tushare` `daily_basic`/行情接口 | 同一张表只保留一套主口径；若换源，写明换源原因、接口名和时间戳 |
| 一致预期 | `$akshare` 盈利预测接口，如 `stock_profit_forecast_ths` | `$akshare` 备用盈利预测接口，如 `stock_profit_forecast_em` 全量过滤 | `$wencai-query` 分年查询“<标的> 2026/2027/2028 预测净利润 EPS 预测机构数” | 单家预测不得冒充一致预期；接口结果必须保留机构数、接口名、抓取日期和字段名 |
| 财务窄字段 | facts_core / PEG-ready 已有结构化字段 | `$tushare` `income`/`balancesheet`/`cashflow`/`fina_indicator` | `$akshare` 财务报表接口 | API 字段必须和 Fact-ID 或报告字段做口径校验；不得用净利润替代 EBIT |
| 公告、权益分派、异常波动 | 已有 facts_core / evidence_index 结构化事实 | `$akshare` 公告接口 | `$wencai-query` 公告类查询 | 实施公告、除权日、转增后股本必须记录公告标题、日期和接口来源 |
| 预测线索交叉检查 | `$akshare` 预测明细接口 | `$wencai-query` 分年查询 | 无；失败即记录 `data_gap` | 不使用非接口页面、公开搜索或手工摘录作为数据源 |

使用 `$wencai-query` 作为 fallback 时：

- 先把缺口改写成一句具体问财查询，例如“603629 利通电子 2026年 2027年 2028年 机构一致预期净利润 EPS 预测机构数”。
- 默认用 `query_type=stock`；轻量查询先匿名运行，失败或字段不完整再提示需要 `WENCAI_COOKIE`。
- 输出必须保留“问财查询句、抓取日期、返回行数、关键列、接口状态”。若问财返回空表或非机构预测，保留 `data_gap`。
- 问财适合补线索、筛表和交叉检查；不得替代公告事实、定期报告事实或 AkShare/Tushare 已能取得的主接口字段。
- 对 A 股一致预期，宽泛问法失败或误路由时必须按年份拆分查询；分年查询仍失败后，才能把 Wencai 记为不可用。

估值输出模式：

| 模式 | 触发条件 | 允许输出 | 必须标注 |
| --- | --- | --- | --- |
| `consensus_mode` | 一致预期可用，且 PEG-ready 自有正常/乐观利润锚完整 | 正式 PEG/动态 PE 估值；正常/乐观目标市值必须用自有利润锚；一致预期差、当前市值隐含预期和一致预期对照 | `正式 PEG 估值`，说明一致预期来源、机构数和日期；标注“目标市值锚=自有正常/乐观利润锚，一致预期只作市场对照” |
| `no_consensus_mode` | fallback 后一致预期仍为 `data_gap` 或只有 `single_or_unverified_forecast`，但 PEG-ready 自有利润锚、YoY/CAGR、市场口径和质量说明完整 | 无一致预期版自建情景估值、正常/乐观情景目标市值、当前市值反推、触发/降级条件、证伪点 | `无一致预期版自建情景估值`；`一致预期差=N/A`；`不是市场一致预期差驱动的正式估值` |
| `preparation_only` | PEG-ready 包缺失，或自有利润锚、YoY/CAGR、市场口径、现金流质量字段不完整 | 准备清单、缺口表、压力测试 | 不得输出目标市值或目标价 |

`no_consensus_mode` 纪律：

- 可以输出“情景目标市值”或“自建情景估值区间”，但标题、摘要、文件名和最终回复必须显著标注 `no_consensus` 或“无一致预期版”。
- 不得输出“相对一致预期上修空间”“一致预期差”“市场预期低估”等结论；这些字段统一写 `N/A`。
- 不得把社区预测、问财无预测结果、单家未回源预测或公司业绩预告替代为一致预期。
- 目标市值必须绑定 PEG-ready 自有利润锚、动态 PEG/复合 PEG 假设、当前年份纪律、触发条件和证伪点。

可选，仅在确实影响目标价时补充：

- SOTP：控股上市子公司、参股资产、少数股东权益、可能重复计算的资产。
- 同行估值：只作为估值容忍度背景，除非用户明确要求横向比较。

## Non-negotiables

1. `consensus_mode` 正式估值必须同时覆盖：
   - 市场一致预期
   - 本 skill 读取或生成的 PEG-ready 数据包
   - Catalyst 前置检查结论：`catalyst_precheck` 或近期 `integrated_update`
   - PEG-ready 数据包中的自有正常/乐观目标市值利润锚，以及市场一致预期对照
   - 动态 PEG
   - 复合 PEG
   - 当前市值隐含利润
   - 正常与乐观目标市值
   - 当当前年份为 2026 年时，必须先计算 `2027E` 一年远期动态 PEG 和 `2027E` 一年远期复合 PEG，再讨论是否切换到 2028E
   - 若一致预期缺失但 PEG-ready 自有利润锚完整，进入 `no_consensus_mode`，可输出自建情景目标市值，但必须把一致预期差写为 `N/A`，并明确不是市场一致预期差驱动的正式估值。
   - 三视角估值结论：`Auditor View`、`PM View`、`Catalyst View`
2. 必须区分：
   - 市场一致预期
   - PEG-ready 自有利润锚
   - 公司公告或财报事实
   - 卖方或市场口径
   - 合理推断
   - 情景假设
3. 禁止把市场一致预期利润直接当作正常/乐观目标市值分母：
   - 一致预期是市场对照锚，用于判断市场隐含要求、预期差、机构预测方向和当前市值是否已经交易到一致预期。
   - 正常目标市值使用 `own_normal_profit_*`；乐观目标市值使用 `own_bull_profit_*`。
   - 若用户明确要求“按一致预期给估值”，只能另列 `consensus-implied reference`，并在摘要、表名和结论中注明这不是本 skill 的正常/乐观主估值。
   - 若自有利润锚缺失或口径未校验，不得用一致预期替代输出目标市值；应进入 `preparation_only` 或先补齐 PEG-ready 包。
4. 禁止把“审计口径”作为唯一估值结论：
   - `Auditor View` 只按已披露、审计、公告和财报口径判断底线、现金流、风险和证伪条件。
   - `PM View` 按市场正在交易的未来 12-24 个月利润、一致预期/自有利润桥和同行估值，判断当前贵不贵以及合理 PEG/PE 区间。
   - `Catalyst View` 承接前置 catalyst 检查，说明哪些关键催化兑现后允许 PEG 系数上修或估值年份切到更远期，哪些未兑现时必须锁回 Auditor/PM 基准。
   - 最终结论应由三视角综合得出；`Auditor View` 是底线和风险，不得单独替代 PM 定价判断。
5. PEG 不能机械使用。必须检查低基数、周期峰值、一次性并表、非经常性损益、补库、涨价、订单前置和利润持续性。
   - 必须说明本次采用的 PEG 档位是否符合 `peg_valuation_handoff` 的核心因子接口、情景准入和年份纪律。
   - 若突破 handoff 的情景边界，必须给出新增证据或市场环境变化；若收紧，必须说明利润质量、证伪压力、现金流约束或年份切换不足。
6. 默认输出只保留**正常**和**乐观**两档目标市值；禁止输出保守估值、悲观估值或下限估值。风险以“证伪点”表达。
7. SOTP 与同行估值默认降级为辅助模块：
   - SOTP 只有在控股上市子公司或参股资产会明显扭曲估值时才做。
   - 同行估值只用于说明市场是否处在高估值容忍环境，不作为核心目标价锚。
8. 估值年份纪律：
   - 当前年份为 2026 年时，主估值年份默认是 `2027E`；正常/乐观目标市值的利润锚分别为 `own_normal_profit_2027E` 和 `own_bull_profit_2027E`。
   - 当前市值可同时除以自有正常、自有乐观和一致预期 2027E 利润来反推市场已经交易到哪一步；目标市值主表不得用一致预期替代自有利润锚。
   - 不得跳过 `2027E`，直接用 `2028E` 预测利润作为正常或乐观目标市值锚。
   - `2028E` 只能作为“估值年份切换/远期乐观情景”单独列示，且必须先回答：2027E PEG 是否已经合理、市场为什么愿意提前交易 2028E、触发条件是什么。
   - 如果用户明确要求看 2028E，也必须同时保留 2027E 守门表，不能只给 2028E 目标市值。

## PEG-ready Package

正式估值前优先读取已有 PEG-ready 数据包；若缺失，由本 skill 在当前研究目录内生成。不得为了 PEG 估值调用 `$financial-modeling`，也不得把三表模型或其他估值文件改名为 PEG-ready 包。

一致预期可用时，正式 PEG 仍进入 `consensus_mode`，但这只表示“市场一致预期可用于对照”，不表示目标市值分母使用一致预期。正常/乐观目标市值必须分别使用 PEG-ready 自有正常/乐观利润锚；一致预期用于市场隐含预期、预期差、机构预测方向和 `consensus-implied reference`。只有一致预期不可用且自有利润锚、YoY/CAGR、市场口径和质量说明完整时，才进入 `no_consensus_mode`。

最低字段：

| 字段 | 用途 |
| --- | --- |
| `valuation_date` | 固定股价、市值、预测和一致预期的日期 |
| `current_market_cap` / `current_price` / `shares_outstanding` | 计算 Forward PE、当前市值隐含和目标市值 |
| `profit_metric` | 明确使用扣非利润、经营利润或调整后归母利润 |
| `consensus_profit_2026E/2027E/2028E` | 一致预期对照、市场隐含反推和预期差，不作为默认目标市值分母 |
| `own_normal_profit_2026E/2027E/2028E` | 正常目标市值利润锚；必须完成口径统一、YoY/CAGR 和质量校验 |
| `own_bull_profit_2026E/2027E/2028E` | 乐观目标市值利润锚；必须绑定触发条件和质量校验 |
| `profit_yoy_2027E/2028E` | 动态 PEG 增速 |
| `profit_cagr_2025A_2027E` / `profit_cagr_2026E_2028E` | 复合 PEG 增速 |
| `non_recurring_items` / `minority_interest` / `investment_income` | 利润质量和重复计算检查 |
| `cashflow_quality_note` | OCF、营运资本和利润含金量对 PEG 质量折价的约束 |
| `source_notes` | 预测和市场数据来源 |

`peg_valuation_handoff` 只提供 PEG 档位、情景准入、质量折价和年份切换边界；不得用它补齐上述利润锚、YoY 或 CAGR。

若旧版 PEG-ready 包使用 `own_base_profit_*` 字段，读取时统一映射为 `own_normal_profit_*`；正式输出中只写“正常情景/正常估值”，不写 Base、保守或悲观。

若本 skill 尝试生成或补齐后仍缺关键字段，必须停止在正式估值前，并输出：

```text
缺失的 PEG-ready 字段：
可从 peg_valuation_handoff 继承的规则：
必须由本 skill 补齐或从事实/一致预期源获取的利润/YoY/CAGR/现金流质量字段：
本次不能输出的估值结论：
```

## Core Concepts

### 动态 PEG

用于回答：某一年利润增长有多快，市场可给多少当年 PE。

```text
动态 PEG = Forward PE / 对应年度净利润增速
对应 PE = 动态 PEG × 对应年度净利润增速
目标市值 = 利润锚 × 对应 PE
```

常用方式：

- 正常：动态 PEG 1.0-1.2x。
- 乐观：产业主升浪或强牛市中，动态 PEG 1.3-1.5x。
- 高潮：超过 1.5x 时必须标注为趋势/泡沫上沿，不作为基础估值中枢。

### 复合 PEG

用于避免单年增速被低基数、涨价、补库或高景气季度扭曲。

```text
复合 PEG = Forward PE / 未来 2-3 年归母净利润 CAGR
对应 PE = 复合 PEG × 未来 2-3 年利润 CAGR
目标市值 = 利润锚 × 对应 PE
```

优先使用：

- 当前年份为 2026 年时，优先用 `当前市值 / 2027E 利润` 得到一年远期 Forward PE。
- 用 `2025A-2027E` 或 `2026E-2028E` CAGR 做复合增速，但 PE 分母仍先用 `2027E` 利润；不要因为 CAGR 终点到 2028E 就把目标市值锚直接换成 2028E。
- 结论必须说明复合 PEG 与动态 PEG 是否收敛。

### 不推荐主用 TTM PEG

`TTM PE / TTM 净利润同比增速` 只适合快速观察，不适合主结论。原因是 TTM 增速容易被低基数、周期修复、补库、涨价和单季高景气扭曲。

## Workflow

### Step 0: 输入压缩与估值闸门

- 建立本次估值的输入清单：Catalyst 前置检查、PEG-ready 数据包、peg_valuation_handoff、facts_core 可用性、需要片段复核的前置文件。
- 先完成 Step 0A，再判断 PEG-ready 是否完整；不要因为已有 PEG-ready 包就跳过 catalyst precheck。
- 若 PEG-ready 数据包完整且 catalyst precheck 已完成，直接进入 Step 1；不要为了“再确认”全文读取 `final_report` 或 `profit_bridge`。
- 若 PEG-ready 数据包缺字段，先输出缺口清单；只对缺字段对应的前置文件做关键词定位和片段读取。
- 任何新增事实都优先写成 `Fact-ID` 或“来源 + 字段 + 日期”的短注释，不把长段证据复制进估值报告。

### Step 0A: Catalyst Precheck

估值前必须先执行 `$equity-catalyst-tracker` 前置检查；若无法嵌套调用 skill，则在当前研究目录生成 `<标的>_catalyst_precheck.md`。

`catalyst_precheck` 输出最小结构：

```text
基准假设：
最近增量证据：
Catalyst log：
Stage scorecard：
红黄绿灯：
未来 1-3 个月 watchlist：
对 PEG 系数的影响：
对估值年份切换的影响：
必须锁回 Auditor/PM 基准的证伪条件：
```

在 PEG 主报告中，用一张小表消费 catalyst 结论：

| 检查项 | Catalyst precheck 结论 | 对 PEG/PE 的处理 |
| --- | --- | --- |
| 阶段 | 预期型/半兑现型/兑现型/右侧重估型/高潮型/证伪型 |  |
| 新增证据强度 |  |  |
| 是否支持乐观 PEG |  |  |
| 是否支持切远期年份 |  |  |
| 必须证伪/降级的条件 |  |  |

### Step 1: 当前市值与估值锚

- 先标记本次输出模式：`consensus_mode`、`no_consensus_mode` 或 `preparation_only`。
- 在 `consensus_mode` 下，同时标记目标市值锚口径：`target_anchor=own_profit_anchors`。这意味着一致预期可用但不作为正常/乐观目标市值分母。
- 确认股价、总市值、股本、TTM PE、静态 PE、PB；若 PEG-ready 包缺市场字段或字段过期，按“备用数据源阶梯”只选一个主行情源刷新，失败后再 fallback。
- 判断当前阶段：预期型、半兑现型、兑现型、右侧重估型、高潮型、证伪型。
- 判断市场当前用什么估值锚：次年 PE、远期利润、动态 PEG、复合 PEG、产业平台溢价，还是情绪溢价。

若存在 `peg_valuation_handoff`，先建立“因子消费规则检查表”：

| 项目 | handoff 规则 | 本次估值采用 | 是否突破边界 | 原因 |
| --- | --- | --- | --- | --- |
| 主估值框架 |  |  |  |  |
| 主年份纪律 |  |  |  |  |
| 正常情景可用因子 |  |  |  |  |
| 乐观情景可用因子 |  |  |  |  |
| 质量折价因子 |  |  |  |  |
| 年份切换触发条件 |  |  |  |  |
| 现金流质量约束 |  |  |  |  |

PEG/PE 容忍度判断必须来自前置投研产物中的 `Fact-ID`、摘要、必要片段和 `peg_valuation_handoff` 的消费规则：主线类型、兑现阶段、利润质量、订单可见度、第二曲线、竞争壁垒、市场环境和证伪压力。利润预测决定 PE 分母；投研因子和质量约束决定 PEG/PE 容忍度。

在 Step 1 末尾先写三视角框架，不急着给最终目标市值：

| 视角 | 输入口径 | 解决的问题 | 本次初步结论 |
| --- | --- | --- | --- |
| Auditor View | 已披露/审计/公告/财报 | 底线、风险、现金流、证伪 |  |
| PM View | 未来 12-24 个月利润、一致预期/自有利润桥、同行估值 | 当前贵不贵、合理 PEG/PE 区间 |  |
| Catalyst View | catalyst precheck、订单/客户/财报/产业事件 | 是否允许上修 PEG 或切远期年份 |  |

### Step 2: 市场一致预期

建立一致预期表：

| 年份 | 一致预期净利润 | 一致预期 EPS | 预测机构数 | 近 1-3 个月变化 | 口径和来源 |
| --- | ---: | ---: | ---: | --- | --- |
| 2026E |  |  |  |  |  |
| 2027E |  |  |  |  |  |
| 2028E |  |  |  |  |  |

判断一致预期是在上修、横盘还是下修。成长股估值对“预期变化方向”高度敏感。

若机构一致预期主接口不可用，按“Skill/API 数据源阶梯”依次调用 `$akshare` 备用预测接口和 `$wencai-query` 分年查询。禁止使用非接口页面、公开搜索或手工研报线索。fallback 结果必须分成三类：

- A 股标的必须先完成 `references/a-share-consensus-preflight.md` 中的 AkShare 预测接口、AkShare 备用预测接口和 Wencai 分年查询，并把成功/失败接口写入 `source_notes` 或单独的数据源检查文件。

- `consensus_available`：有机构数、预测年份、净利润/EPS 和发布日期，可进入正式 PEG。
- `single_or_unverified_forecast`：只有单家或无法回源预测，只能做参考，不可称为一致预期。
- `data_gap`：未取得可用预测，`consensus_mode` 正式 PEG 阻断；若 PEG-ready 自有利润锚、YoY/CAGR、市场口径和质量说明完整，则切换到 `no_consensus_mode`，允许输出明确降级的自建情景目标市值和当前市值反推；若 PEG-ready 也不完整，则只允许压力测试和准备清单。

### Step 3: PEG-ready 利润锚对照

从 PEG-ready 数据包读取正常和乐观两档，和一致预期并排比较：

| 年份 | 一致预期净利润 | 自有正常 | 自有乐观 | 关键差异 | 证据强度 |
| --- | ---: | ---: | ---: | --- | --- |
| 2026E |  |  |  |  |  |
| 2027E |  |  |  |  |  |
| 2028E |  |  |  |  |  |

差异来源必须拆到收入、ASP、毛利率、费用率、订单出货、扩产爬坡、并表比例、投资收益或非经常性项目。

锚定规则必须显式写出：

- 正常目标市值锚 = `own_normal_profit_2027E`（或当前年份对应的下一年自有正常利润锚）。
- 乐观目标市值锚 = `own_bull_profit_2027E`（或当前年份对应的下一年自有乐观利润锚）。
- 一致预期利润只进入“市场隐含预期 / 一致预期差 / 当前市值对照”表。若一致预期高于自有乐观，必须写成“当前市场隐含要求偏进攻”，不得写成“目标市值上修依据”。
- 若自有正常/乐观利润锚缺失、未校验或与 handoff 口径冲突，不得用一致预期替代目标市值锚；先补 PEG-ready 包或进入 `preparation_only`。

若处于 `no_consensus_mode`：

- 一致预期列保留 `data_gap` 或 `N/A`，不要删除该列。
- 新增一列 `模式处理`，写明“无一致预期，以下为自有情景锚，不代表市场一致预期”。
- 估值差异不写“预期差”，改写为“当前市值对自有情景的隐含要求”。

### Step 4: 动态 PEG 估值

只输出正常和乐观两档：

| 情景 | 利润锚 | 净利润增速 | 动态 PEG | 对应 PE | 目标市值 | 触发条件 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 正常 |  |  |  |  |  |  |
| 乐观 |  |  |  |  |  |  |

要求：

- 当前年份为 2026 年时，利润锚必须先使用 2027E 自有利润锚：正常情景用 `own_normal_profit_2027E`，乐观情景用 `own_bull_profit_2027E`。只有在完成 2027E 守门后，才允许把 2028E 作为“估值年份切换”扩展情景。
- 禁止把 `consensus_profit_2027E` 放入正常/乐观动态 PEG 主表。若需要展示，另列“consensus-implied reference / 一致预期隐含估值参考”，并标注不是目标市值主结论。
- 增速必须说明相对哪一年增长，例如 2027E 相对 2026E。
- 乐观 PEG 不能只因为用户想象牛市就给，必须绑定业绩、订单、毛利率、板块动能或估值年份切换触发条件。
- 若为 `no_consensus_mode`，表名写成“无一致预期版动态 PEG 情景估值”，目标市值列写“情景目标市值”，并在表下注明“该区间由自有利润锚和 PEG 假设得出，不代表一致预期差结论”。

### Step 5: 复合 PEG 估值

只输出正常和乐观两档：

| 情景 | PE 分母/利润锚 | CAGR 区间 | 复合增速 | 复合 PEG | 对应 PE | 目标市值 | 触发条件 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| 正常 |  |  |  |  |  |  |  |
| 乐观 |  |  |  |  |  |  |  |

要求：

- 当前年份为 2026 年时，必须先输出 `2027E 一年远期复合 PEG 守门表`：

| 情景 | 2027E 利润锚 | CAGR 区间 | 复合增速 | 复合 PEG | 对应 PE | 2027E 锚目标市值 | 判断 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| 正常 |  |  |  |  |  |  |  |
| 乐观 |  |  |  |  |  |  |  |

- CAGR 可用 `2025A-2027E` 或 `2026E-2028E`，但这一张守门表的目标市值必须由 `2027E 利润锚 × 对应 PE` 得出。
- `2027E 利润锚` 在正常/乐观主表中分别指 `own_normal_profit_2027E` 和 `own_bull_profit_2027E`，不是 `consensus_profit_2027E`。
- 若再列 `2028E 估值年份切换表`，必须单独标注为远期乐观/切换情景，不能混入正常目标市值。
- 复合 PEG 应和动态 PEG 互相校验：若差异很大，说明单年增速可能失真。
- 最终目标市值优先取 2027E 动态 PEG 和 2027E 复合 PEG 的收敛区间；2028E 只作为“上沿来自年份切换”的附加判断。
- 若为 `no_consensus_mode`，最终区间只能称为“自建情景估值区间”或“情景目标市值区间”，不得称为“市场一致预期修正后的合理市值”。

### Step 6: 当前市值隐含预期

用当前市值反推市场已经买到哪一步：

| 当前市值 / 利润锚 | 对应 PE | 若用 PEG 反推隐含增速 | 判断 |
| --- | ---: | ---: | --- |
| 当前市值 / 正常利润锚 |  |  |  |
| 当前市值 / 乐观利润锚 |  |  |  |
| 当前市值 / 一致预期利润锚（仅市场对照） |  |  |  |

重点回答：

```text
当前价格已经定价到正常、乐观，还是一致预期之外？
后续上涨需要利润上修、PE 上修，还是估值年份切换？
```

一致预期行只能用于判断市场已经交易到哪一步；不得从该行直接导出正常/乐观目标市值。

若为 `no_consensus_mode`，`当前市值 / 一致预期利润锚` 行写 `N/A`，并额外输出：

| 市场给定 PE | 当前市值所需利润 | 与自有情景关系 |
| ---: | ---: | --- |
| 30x |  |  |
| 40x |  |  |
| 50x |  |  |
| 60x |  |  |

### Step 7: 市场环境与 PEG 容忍度

用一句话或小表判断市场状态：

| 市场状态 | PEG 容忍度 |
| --- | --- |
| 熊市/流动性收缩 | PEG 要求严格，1.0x 以上难持续 |
| 震荡市 | 重点看业绩兑现，PEG 1.0-1.2x |
| 结构牛市 | 龙头可给 1.2-1.4x |
| 全面牛市 | 市场可能提前交易远期利润，1.3-1.5x |
| 产业主升浪 | 稀缺龙头可阶段性给 1.3-1.5x，甚至短期更高 |
| 高潮期 | PEG 失真，重点看利好钝化、拥挤度和回撤风险 |

必须回答：当前市场环境是否足以支持乐观 PEG。

### Step 8: SOTP 与同行估值（可选、压缩）

默认不要展开大表。只有在以下情况才写：

- 控股上市子公司或参股资产价值足以改变目标市值区间。
- 合并利润与资产市值可能被重复计算。
- 用户明确要求横向比较同行。

输出原则：

- SOTP 只说明是否重复计算、是否需要扣除或折价，不作为核心估值锚。
- 同行估值只说明“估值容忍度背景”，不替代 PEG 目标价。
- 若需要同行估值，只列 3-6 个可比公司和估值容忍度结论；不要写完整同行研究。

### Step 9: 最终输出

最终报告优先输出：

```text
输出模式：consensus_mode / no_consensus_mode / preparation_only
输入读取范围：catalyst_precheck 或 integrated_update / PEG-ready / handoff / facts_core / 片段复核文件
估值模式：
目标市值锚口径：自有正常/乐观利润锚；一致预期只作市场对照（若适用）
模式降级说明（如适用）：
估值结论：
使用的 PEG-ready 数据包：
因子消费规则结论：
本次采用的 PEG 档位：
Auditor View：
PM View：
Catalyst View：
三视角综合权重/优先级：
是否沿用 handoff 建议；若调整，原因是什么：
动态 PEG 结论：
复合 PEG 结论：
一致预期差：
当前市值隐含预期：
一致预期隐含参考（仅对照，非主目标市值）：
正常目标市值：
乐观目标市值：
2027E 一年远期复合 PEG 守门结论：
是否允许切换到 2028E：
倍数上修条件：
倍数下修条件：
从正常走向乐观的触发条件：
最关键证伪点：
下一次需要跟踪的数据：
```

`no_consensus_mode` 的最终输出必须额外包含：

```text
无一致预期声明：
本次不能回答的问题：相对一致预期上修/下修、市场预期差、机构预测变化
本次可以回答的问题：当前市值需要多少利润/PE 支撑、自有正常/乐观情景下的目标市值区间、触发/证伪条件
```

目标市值表只允许保留正常和乐观；利润锚必须使用自有正常/乐观利润锚。若为 `no_consensus_mode`，标题和列名必须写“情景目标市值”：

| 情景 | 利润锚 | PEG | 对应 PE | 目标市值 | 相对当前空间 | 触发条件 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 正常 |  |  |  |  |  |  |
| 乐观 |  |  |  |  |  |  |

当当前年份为 2026 年时，表内 `利润锚` 默认写 `2027E`。若另列 2028E，上表之后加一个小节：

```text
2028E 估值年份切换情景：
- 是否允许切换：
- 必要触发条件：
- 2028E 利润锚：
- 对应 PE/PEG：
- 目标市值上沿：
- 为什么不能把它当作正常估值：
```

风险不要另列保守/悲观/下限估值大表，改用证伪点表达：

- 单季利润低于关键平台。
- 毛利率回落。
- 订单/出货/现金流不匹配。
- 高端产品占比不能验证。
- 板块估值从主升浪退潮。

## Output Files

估值产物必须写入当前任务目录下的 `research_artifacts/<股票代码或公司简称>/`，不得散落到任务根目录或临时目录。若目录不存在，先创建目录再写文件。

`consensus_mode` 输出：

```text
research_artifacts/<股票代码或公司简称>/
  <标的>_peg_ready_package.md
  <标的>_catalyst_precheck.md（若本次生成；若复用 integrated_update，在 deepdive 中注明）
  <标的>_peg_valuation_deepdive.md
  <标的>_peg_valuation_scorecard.md
```

`no_consensus_mode` 输出：

```text
research_artifacts/<股票代码或公司简称>/
  <标的>_peg_ready_package.md
  <标的>_catalyst_precheck.md（若本次生成；若复用 integrated_update，在 deepdive 中注明）
  <标的>_no_consensus_peg_valuation_deepdive.md
  <标的>_no_consensus_peg_valuation_scorecard.md
```

不要覆盖已有 `<标的>_valuation_scorecard.md`；本 skill 的正式输出使用 `peg_valuation_scorecard` 或 `no_consensus_peg_valuation_scorecard`。

文件风格：

- `peg_valuation_deepdive`：以动态 PEG、复合 PEG、目标市值区间和触发条件为主。
- `peg_valuation_scorecard`：给出简短评分、核心区间、关键证伪点，并同时列示 Auditor View、PM View、Catalyst View、权重/优先级、当前估值所在区间和触发/证伪条件。
- `no_consensus_peg_valuation_deepdive`：以自有正常/乐观利润锚、情景目标市值、当前市值反推和触发/证伪条件为主；必须在标题或摘要写“无一致预期版”。
- `no_consensus_peg_valuation_scorecard`：结构化输出模式降级、情景区间、不能回答的问题、关键触发和证伪点，并同样保留三视角判断。
- 避免把 SOTP、同行估值、保守估值、悲观估值或下限估值写成主章节；除非用户明确要求。
- 文件标题或摘要必须标注“PEG/动态 PE 估值”。
- 若一致预期缺失，文件标题或摘要必须标注“无一致预期版自建情景估值”，不要标注为“正式 PEG 估值”。
- `peg_valuation_deepdive` 不复述前置研究报告全文；只保留影响 PEG 档位、利润锚、质量折价、年份切换和证伪条件的证据摘要。
- `peg_valuation_scorecard` 应服务聚合器和最终回复，优先结构化输出关键数字、结论、触发条件和缺口，不重复 `peg_valuation_deepdive` 的推理长段。

最终回复用户时，说明估值使用了哪些前置文件、哪些数据仍缺失，以及估值结论是否改变原主线判断。

## Handoff Use

`peg_valuation_handoff` 是 PEG 档位和年份纪律的辅助输入，不是正式估值的硬门槛。

使用规则：

- 若存在较新的 `<标的>_peg_valuation_handoff.md`，优先消费其情景准入、质量折价、年份切换和 PEG 系数影响。
- 若 handoff 缺失、过期或只列因素不解释系数影响，不停止估值；改用 PEG-ready、catalyst precheck、facts_core 和必要片段完成估值，并把 handoff 缺口写入 scorecard。
- handoff 不能替代 PEG-ready；利润锚、YoY、CAGR、市值和一致预期字段仍以 PEG-ready 或本 skill 补齐结果为准。
- 若突破 handoff 边界，必须说明新增证据或市场环境变化；若没有 handoff，则降低乐观 PEG 档位置信度，并默认不主动切远期年份。
