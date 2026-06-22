---
name: dcf-valuation-workflow
description: DCF-only valuation workflow orchestrator for equity research. Use when the user asks for DCF估值, DCF闭环, intrinsic value, Formal DCF, Scenario DCF, Reverse DCF, or wants a one-pass workflow that first prepares financial-modeling DCF-ready inputs and then runs dcf-model outputs. This skill coordinates financial-modeling to dcf-model only; do not use it for PEG valuation, PEG+DCF aggregation, or 综合估值.
---

# DCF Valuation Workflow

## Overview

This skill is the DCF control layer. It does not build the three-statement model itself, does not calculate DCF formulas itself, and does not combine PEG with DCF.

It orchestrates two independent skills:

```text
financial-modeling -> DCF-ready package / UFCF bridge / assumption ledger / data gaps
dcf-model -> Formal, Scenario, or Reverse DCF model / summary / validation
```

## Core Rules

- Always use `$financial-modeling` before any forward DCF path.
- Use `$dcf-model` only after a DCF-ready handoff, assumption ledger, or explicit data-gap decision exists.
- Keep PEG fully out of scope. Do not read PEG target market cap, PEG bands, or PEG scorecards to calibrate WACC, terminal value, exit multiple, or DCF equity value.
- Do not output buy/sell advice, target position size, or certainty language.
- If the DCF inputs are not strong enough for Formal DCF, downgrade to Scenario DCF, Reverse DCF, or preparation-only instead of inventing precision.
- If the user asks to compare PEG and DCF, complete this DCF workflow first and leave comparison to the report layer; do not recreate a PEG+DCF aggregator.

## Progressive Disclosure

Read these references as needed:

- Always read [workflow.md](references/workflow.md) before acting.
- Read [input-contract.md](references/input-contract.md) when preparing, checking, or repairing DCF-ready inputs.
- Read [output-checklist.md](references/output-checklist.md) before final delivery or when deciding whether the DCF workflow is complete.

Also load and follow the upstream skill files at the point of use:

```text
/Users/a/.codex/skills/financial-modeling/SKILL.md
/Users/a/.codex/skills/dcf-model/SKILL.md
```

## Workflow

1. Identify the company, ticker, currency, artifact directory, and available research files.
2. Run the financial-modeling stage to create or verify the DCF-ready package.
3. Decide the DCF mode using the workflow reference:
   - Formal DCF
   - Scenario DCF
   - Reverse DCF
   - Preparation-only
4. Run the dcf-model stage using only admitted DCF inputs.
5. Validate formulas, source comments, assumption ledger completeness, terminal constraints, UFCF tie-out, and EV-to-equity bridge.
6. Return the generated files, mode, validation status, and remaining data gaps.

## Required Artifact Boundary

Default research directory:

```text
research_artifacts/<target>/
```

Financial-modeling stage should produce or confirm:

```text
<target>_dcf_ready_package.md
<target>_dcf_assumption_ledger.md
<target>_dcf_data_gaps.md
```

DCF-model stage should produce one mode-specific set:

```text
Formal:
  <target>_dcf_model.xlsx
  <target>_dcf_summary.md
  <target>_dcf_validation.json

Scenario:
  <target>_scenario_dcf_model.xlsx
  <target>_scenario_dcf_summary.md
  <target>_scenario_dcf_validation.json
  <target>_dcf_assumption_ledger.md

Reverse:
  <target>_reverse_dcf_summary.md
  <target>_dcf_assumption_ledger.md

Preparation-only:
  <target>_dcf_data_gaps.md
```

## Non-Negotiables

1. No forward DCF without a UFCF bridge.
2. No Formal DCF without sourced or auditable Revenue, EBIT, Tax, D&A, Capex, Delta NWC, UFCF, cash, debt, shares, WACC inputs, and terminal assumptions.
3. No non-factual input enters the model without source type, confidence, range, and sensitivity treatment.
4. No D-confidence clue can drive Base or Bull valuation.
5. No net income, adjusted profit, EBITDA, or PEG profit anchor may substitute for UFCF.
6. No DCF delivery is complete without mode label, source/date notes, data gaps, and validation status.
