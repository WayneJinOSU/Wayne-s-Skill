# DCF Input Contract

## Contents

1. Required Fields
2. Source Types
3. Confidence Admission
4. Financial-Modeling Handoff
5. Hard Stops

## 1. Required Fields

The DCF-ready package must cover these fields or list them in data gaps:

| Category | Fields |
| --- | --- |
| Operating forecast | Revenue, revenue growth, EBIT margin, EBIT, tax rate, NOPAT |
| UFCF bridge | D&A, Capex, Delta NWC, UFCF |
| EV bridge | Cash, debt, minority interest / other claims, shares, current price / market cap |
| WACC | Risk-free rate, ERP, beta, cost of equity, pre-tax cost of debt, tax rate, capital structure weights |
| Terminal value | Terminal growth or exit multiple, steady-state margin/cash-flow rationale |
| Evidence | Source comments, source dates, Fact-ID or document reference, confidence, sensitivity treatment |

DCF must use:

```text
UFCF = EBIT * (1 - Tax) + D&A - Capex - Delta NWC
```

It must not replace UFCF with net income, attributable profit, adjusted profit, EBITDA, or PEG profit anchors.

## 2. Source Types

Every input must be tagged:

| Source type | Examples | Model use |
| --- | --- | --- |
| Fact | Annual/interim reports, announcements, audited notes, exchange filings, current market data | Formal or Scenario hard anchor |
| Consensus | Wind, Choice, iFinD, F10, Wencai, sell-side forecast aggregate | Forecast anchor with date and institution count when available |
| Business Inference | Order conversion, capacity ramp, product mix, ASP, margin path, customer validation | Scenario Base/Bull only with triggers and downgrade path |
| Proxy | D&A from revenue or PPE, Delta NWC from revenue change, peer beta, normalized Capex | Scenario or sensitivity; must be ranged |
| Reverse Implied | Current market cap implied UFCF, EBIT margin, terminal FCF | Reverse DCF only; not a forecast |

## 3. Confidence Admission

| Confidence | Meaning | Can enter Base? |
| --- | --- | --- |
| A | Direct fact or high-quality consensus | Yes |
| B | Multi-source supported inference or robust proxy | Yes, with sensitivity |
| C | Plausible but weakly sourced inference/proxy | Scenario or sensitivity only |
| D | Thin clue, theme, unverified single source, market rumor | No; tracking only |

Non-factual inputs must include:

```text
field
value_or_range
source_type
source_or_reasoning
confidence
sensitivity_treatment
model_use
```

## 4. Financial-Modeling Handoff

`$financial-modeling` should output:

```text
<target>_dcf_ready_package.md
<target>_dcf_assumption_ledger.md
<target>_dcf_data_gaps.md
```

The handoff should be compact and include:

- Historical anchors and latest base year.
- Projection years and scenario labels.
- Revenue, EBIT, tax, D&A, Capex, Delta NWC, UFCF by year.
- Cash, debt, shares, minority interest / other claims.
- WACC and terminal assumptions, or gaps if not yet sourced.
- Source comments and confidence for every driver.
- Data gaps and whether each gap blocks Formal DCF, Scenario DCF, or only sensitivity.

Financial-modeling does not output target price, target market cap, valuation conclusion, or buy/sell advice.

## 5. Hard Stops

Stop Formal DCF when:

- UFCF bridge is missing or does not tie out.
- Capex or Delta NWC is unavailable and not defensibly proxied.
- WACC inputs lack source or range.
- Terminal growth is greater than or equal to WACC.
- Source comments are missing for hardcoded Excel inputs.

Stop Scenario DCF when:

- A key non-factual input lacks range, source type, confidence, or sensitivity treatment.
- D-confidence clues drive Base or Bull.
- Terminal value dominates without a steady-state rationale.

Use Reverse DCF instead of forward DCF when:

- Current market value is known, but forward UFCF cannot be bounded.
- The useful output is market-implied cash-flow requirements rather than fair value.
