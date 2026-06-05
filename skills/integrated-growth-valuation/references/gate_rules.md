# Gate Rules

正式交付前运行 `scripts/valuation_gate.py`。

## Required Files

默认检查：

```text
<标的>_valuation_aggregate.md
<标的>_valuation_scorecard.md
<标的>_peg_valuation_deepdive.md
<标的>_peg_valuation_scorecard.md
<标的>_dcf_summary.md
<标的>_dcf_validation.json
```

若 PEG 或 DCF 上游输出缺失，只能输出缺口清单，不能称为正式聚合完成。

## Required Content

`valuation_aggregate` 至少应出现：

```text
PEG
DCF
差异
跟踪
证伪
```

若报告声称完成正式 DCF，建议同时检查：

```text
<标的>_dcf_model.xlsx
<标的>_dcf_summary.md
<标的>_dcf_validation.json
```

`dcf_summary.md` 应至少包含 Revenue、EBIT、Tax、NOPAT、D&A、Capex、ΔNWC、UFCF、Discount factor、PV of UFCF、Terminal value、Enterprise value、Equity value、Value per share、WACC build-up 和 sensitivity。

`dcf_validation.json` 应来自 `/Users/a/.codex/skills/dcf-model/scripts/validate_dcf.py`，且不应存在 formula error 或 terminal growth >= WACC 等 HIGH 问题。

若报告声称完成正式 PEG，建议同时检查：

```text
<标的>_peg_valuation_deepdive.md
<标的>_peg_valuation_scorecard.md
```

这些文件应由 `$growth-stock-valuation` 输出，且应包含动态 PEG、复合 PEG、2027E 守门、当前市值隐含和触发/证伪条件。

## Banned Or Suspicious Content

默认禁止：

```text
买入
卖出
强烈推荐
仓位
梭哈
确定性收益
稳赚
```

可出现但需要人工检查：

```text
目标价
DCF 校验 PEG
PEG 修正 DCF
净利润折现
EBITDA 折现
```

## Failure Handling

- HIGH：必须修复后才能称为正式估值完成。
- MEDIUM：可以交付，但必须在最终回复说明残余风险。
- LOW：格式或可读性问题，建议修复。
