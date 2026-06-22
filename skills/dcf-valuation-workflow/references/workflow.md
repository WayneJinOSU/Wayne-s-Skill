# DCF Workflow

## Contents

1. Intake
2. Financial-Modeling Stage
3. Mode Decision
4. DCF-Model Stage
5. Validation Gate
6. Downgrade Rules

## 1. Intake

Before modeling, identify:

```text
target
ticker / market
currency
latest price / market cap date and source
artifact directory
available research handoff files
available historical financials and consensus
user-requested output format
```

If the target, security identifier, or artifact directory is ambiguous, choose a reasonable directory and state the assumption in the output.

## 2. Financial-Modeling Stage

For any forward DCF path, first use `$financial-modeling`.

Financial-modeling must translate research drivers into a DCF-ready operating forecast:

```text
Revenue -> EBIT -> NOPAT -> UFCF
UFCF = EBIT * (1 - Tax) + D&A - Capex - Delta NWC
```

Required outputs:

```text
<target>_dcf_ready_package.md
<target>_dcf_assumption_ledger.md
<target>_dcf_data_gaps.md
```

The DCF-ready package may be compact. It should contain model fields, source comments, assumption ranges, confidence tags, quality notes, and gaps. It should not repeat the full research thesis.

## 3. Mode Decision

After the financial-modeling stage, choose one mode:

| Mode | Trigger | Required label | Output |
| --- | --- | --- | --- |
| Formal DCF | Core UFCF bridge and WACC/terminal inputs are sourced or auditable | `Formal DCF` | Excel model, summary, validation |
| Scenario DCF | Some fields rely on bounded inference or proxy, but assumptions can be ranged and sensitivity-tested | `Scenario DCF with Assumption Ledger` | Scenario model or markdown summary, ledger, validation if Excel exists |
| Reverse DCF | Forward forecast is too weak, but market cap, EV bridge, WACC, and terminal ranges are available | `Reverse DCF / market-implied cash-flow test` | Reverse summary and ledger |
| Preparation-only | Key drivers have no defensible boundary or source/confidence cannot be stated | `DCF preparation checklist` | Data gaps only |

Formal DCF is not the default. Use the highest mode that the evidence supports.

## 4. DCF-Model Stage

Use `$dcf-model` after the mode decision.

Formal DCF consumes:

```text
<target>_dcf_ready_package.md
<target>_dcf_assumption_ledger.md
```

Scenario DCF consumes the same package plus explicit ranges and sensitivity treatment for non-factual inputs.

Reverse DCF can proceed when financial-modeling cannot build a forward UFCF bridge but can still define:

```text
current market cap / enterprise value
cash, debt, minority interest / other claims
shares
WACC range
terminal growth or exit multiple range
historical or normalized margin/cash-flow anchors
```

Do not use PEG outputs or target market cap as DCF inputs.

## 5. Validation Gate

Before delivery, verify:

```text
mode label is explicit
UFCF bridge ties out
non-factual inputs appear in assumption ledger
source comments exist for hardcoded Excel inputs
terminal growth < WACC
EV-to-equity bridge handles net debt / net cash correctly
sensitivity table center cell equals base case when Excel exists
validation JSON exists when Excel exists
data gaps are listed even when valuation is completed
```

If Excel is produced, run the `dcf-model` validator and formula recalculation flow required by `$dcf-model`.

## 6. Downgrade Rules

Downgrade from Formal to Scenario when:

- D&A, Capex, Delta NWC, WACC, or terminal inputs rely on bounded proxy rather than direct source.
- Forecast revenue or EBIT depends on business inference that needs scenario treatment.
- Source dates, institution counts, or market data quality are incomplete but not unusable.

Downgrade from Scenario to Reverse when:

- Forward UFCF cannot be bounded with enough confidence.
- The more answerable question is what cash-flow path the current market cap implies.

Downgrade to Preparation-only when:

- No credible UFCF bridge can be created.
- Capex or Delta NWC cannot be sourced, proxied, or sensitivity-tested.
- Terminal assumptions would dominate value without any steady-state rationale.
- D-confidence clues would drive the Base or Bull case.
