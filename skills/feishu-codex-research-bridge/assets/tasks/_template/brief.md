# 任务名称

## 隔离规则

本任务必须作为独立投研任务处理。不要继承其他窗口、其他任务目录、其他报告的结论，除非本 brief 明确列为可用材料。

## 研究对象

- 公司/行业：
- 股票代码：
- 市场：

## 任务类型

- 请填写一个明确类型，例如：正式深度报告、估值复盘、爆点跟踪、财报解读、产业链研究：

## Skill 路由

- 推荐 skill：auto
- 是否允许 subagent：yes
- 研究强度：formal

可选 skill：

- `auto`：由队列脚本根据 brief 自动选择
- `supply-chain-agentic-research`：供应链平台型成长股正式深研
- `chassis-growth-agentic-research`：底盘型成长股正式深研
- `equity-catalyst-tracker`：爆点、公告、财报、订单、催化持续跟踪
- `growth-stock-valuation`：成长股 PEG / 动态 PE 独立估值
- `dcf-valuation-workflow`：主控 financial-modeling 与 dcf-model 的 DCF 闭环
- `industry-chain-agentic-research`：行业或产业链正式深研

## 核心问题

1.
2.
3.

## 可用材料

- 本任务目录内的 `sources/`
- 可明确引用的外部路径：

## 输出要求

- 输出文件：不要生成统一 `output.md`；按所选 skill 的原生命名输出核心文件
- 中间产物目录：`research_artifacts/`
- 需要区分：事实、推断、假设、风险、证伪点
- 引用本地材料时标注文件名
- 不要使用其他任务的结论作为前提

核心文件示例：

- `supply-chain-agentic-research` / `chassis-growth-agentic-research`：`research_artifacts/<标的>/<标的>_final_report.md`
- `equity-catalyst-tracker`：`research_artifacts/<标的>/<标的>_integrated_update.md`
- `growth-stock-valuation`：`research_artifacts/<标的>/<标的>_peg_valuation_deepdive.md` 和 `<标的>_peg_valuation_scorecard.md`
- `dcf-valuation-workflow`：`research_artifacts/<标的>/<标的>_dcf_summary.md`、`<标的>_dcf_model.xlsx` 和 `<标的>_dcf_validation.json`；Scenario/Reverse 按模式命名
- `industry-chain-agentic-research`：`research_artifacts/<行业或主线>/<prefix>_final_report_full.md`

## 交付格式

请按所选 skill 的正式流程生成结构化中文投研结果。若 skill 要求中间研究产物、QA、反方审查、估值接力输入或主笔重构文件，必须先写入 `research_artifacts/`，再生成该 skill 的核心终点文件。
