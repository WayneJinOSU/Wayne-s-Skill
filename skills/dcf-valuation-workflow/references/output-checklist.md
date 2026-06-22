# DCF Output Checklist

## Contents

1. Financial-Modeling Outputs
2. DCF Outputs by Mode
3. Summary Requirements
4. Final Response Requirements
5. Forbidden Language

## 1. Financial-Modeling Outputs

Confirm these files exist or state why they were not produced:

```text
<target>_dcf_ready_package.md
<target>_dcf_assumption_ledger.md
<target>_dcf_data_gaps.md
```

Minimum package sections:

```text
base year and currency
historical anchors
scenario assumptions
operating forecast
UFCF bridge
EV bridge inputs
WACC / terminal assumptions or gaps
assumption ledger
data gaps and downgrade implications
```

## 2. DCF Outputs by Mode

Formal DCF:

```text
<target>_dcf_model.xlsx
<target>_dcf_summary.md
<target>_dcf_validation.json
```

Scenario DCF:

```text
<target>_scenario_dcf_model.xlsx       # preferred when Excel is produced
<target>_scenario_dcf_summary.md
<target>_scenario_dcf_validation.json  # required if Excel is produced
<target>_dcf_assumption_ledger.md
```

Reverse DCF:

```text
<target>_reverse_dcf_summary.md
<target>_dcf_assumption_ledger.md
```

Preparation-only:

```text
<target>_dcf_data_gaps.md
```

## 3. Summary Requirements

Every DCF summary must state:

- Mode: Formal / Scenario / Reverse / Preparation-only.
- Why this mode was selected.
- Data date and market data source.
- Forecast period and currency.
- UFCF bridge and key assumptions.
- WACC and terminal assumptions.
- EV-to-equity bridge.
- Sensitivity table or sensitivity narrative.
- Validation status and remaining warnings.
- Data gaps and what would upgrade or downgrade the mode.

Scenario DCF must additionally state:

- Which inputs are Fact, Consensus, Business Inference, Proxy, or Reverse Implied.
- Which inputs are A/B/C/D confidence.
- Which variables are Base, Bull/Bear, or sensitivity-only.

Reverse DCF must additionally state:

- Current market cap / enterprise value bridge.
- Implied UFCF, EBIT margin, FCF margin, or terminal assumption required by current value.
- Comparison against historical facts, consensus, and business-inference ranges.
- Why it is not a fair-value forecast.

## 4. Final Response Requirements

When replying to the user, include:

```text
DCF mode completed
files generated
validation status
key remaining gaps
whether financial-modeling was completed
whether dcf-model was completed
```

If validation could not run, say so plainly and explain why.

## 5. Forbidden Language

Do not write:

```text
DCF proves PEG is reasonable
PEG target market cap was used to calibrate DCF
comprehensive PEG+DCF target price
guaranteed upside
buy / sell / position advice
Formal DCF when the mode is Scenario or Reverse
```
