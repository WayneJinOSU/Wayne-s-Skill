---
name: financial-modeling
description: Build integrated financial models with 3-statement projections, DCF-ready UFCF bridges, working-capital schedules, and debt/interest linkages. Use for income statement, balance sheet, cash flow, and DCF input preparation; do not use for PEG-ready packages or PEG valuation inputs.
---

# Financial Modeling Skill

## Overview

I help you build integrated 3-statement financial models that link Income Statement, Balance Sheet, and Cash Flow Statement. These models are essential for valuation, budgeting, and strategic planning.

**What I can do:**
- Build income statement projections
- Create balance sheet forecasts
- Generate cash flow statements
- Model working capital requirements
- Build debt schedules and interest calculations
- Create scenario analysis (base/bull/bear cases)

**What I cannot do:**
- Access real-time financial data
- Guarantee projection accuracy
- Provide accounting advice
- Replace professional financial analysis

---

## How to Use Me

### Step 1: Provide Historical Data

I need 2-3 years of:
- Income statement (revenue, COGS, operating expenses)
- Balance sheet (assets, liabilities, equity)
- Cash flow statement (optional but helpful)

### Step 2: Define Projection Assumptions

Key drivers:
- Revenue growth rate
- Gross margin
- Operating expense ratios
- Capex as % of revenue
- Working capital days (DSO, DIO, DPO)

### Step 3: Choose Model Scope

- **Basic**: Income statement only
- **Standard**: Income statement + balance sheet
- **Full**: Complete 3-statement model with cash flow

### Research Handoff Mode

When the user provides a research handoff such as `<company>_dcf_financial_model_handoff.md`, use it as the bridge from investment research to modeling:

- Use a single structured financial data source for the three statements by default. Do not pull Tushare, Eastmoney, AkShare, Wencai, and CSV exports in parallel for routine cross-checking. Fallback to another source only when the selected source fails, is inaccessible, lacks required fields, or has an obvious abnormal value.
- Prefer `<company>_facts_core.md` and `Fact-ID` references when available. Do not copy full raw financial statements, announcement lists, Wencai long rows, or Gemini outputs into modeling files.
- If raw CSV files exist, extract only the required narrow fields before reading them into context. Avoid broad text search across `*.csv` files because long rows can dominate the context window.
- First parse the driver map, evidence grades, historical anchors, and scenario ranges. Do not re-write the investment thesis unless needed to explain a driver.
- Treat these six tables as the preferred structured input: historical anchor table; segment driver table; expense and depreciation table; working-capital table; scenario table; data-gap table. If a table is missing, list it in the data-gap checklist before modeling.
- Separate company facts, consensus/market assumptions, and self-built assumptions. If a field is missing, show it in a data-gap checklist instead of inventing precision.
- Build assumptions in this order: revenue drivers -> gross margin -> operating expenses -> D&A/capex -> working capital days -> tax/interest/debt -> minority interest/investment income -> dividends/financing.
- For each driver, preserve source/evidence grade and state whether it belongs in base case, scenario case, or sensitivity only.
- Output a DCF-ready UFCF bridge with `EBIT*(1-Tax)+D&A-Capex-ΔNWC`, plus model checks for balance sheet balance, revenue-profit-cash consistency, and working-capital reasonableness.
- For formal DCF calculation, output `<company>_dcf_ready_package.md` for `/Users/a/.codex/skills/dcf-model`: Revenue, EBIT, tax rate, D&A, Capex, ΔNWC, UFCF, cash, debt, shares, WACC inputs, terminal assumptions, and source comments.
- Do not output `<company>_peg_ready_package.md`; PEG-ready input packs belong to `$growth-stock-valuation`, not financial modeling.
- Keep DCF-ready packages compact: model fields, assumptions, source comments, Fact-ID references, quality notes, and data gaps only. Do not restate every module's thesis or duplicate the full profit bridge.
- Do not output target price, target market cap, buy/sell advice, or final valuation conclusions. For formal valuation, hand off DCF-ready inputs to `/Users/a/.codex/skills/dcf-model`; `integrated-growth-valuation` only aggregates downstream PEG and DCF outputs after both exist.

---

## Model Architecture

### Three-Statement Linkages

```
┌─────────────────────────────────────────────────────────────┐
│                    INCOME STATEMENT                         │
│  Revenue → Gross Profit → Operating Income → Net Income     │
└─────────────────────────┬───────────────────────────────────┘
                          │
        Net Income flows to Retained Earnings
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    BALANCE SHEET                            │
│  Assets = Liabilities + Equity                              │
│  (Must balance via Cash as plug)                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
        Changes in B/S items drive CF Statement
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  CASH FLOW STATEMENT                        │
│  Operating CF + Investing CF + Financing CF = Δ Cash        │
│  Ending Cash flows back to Balance Sheet                    │
└─────────────────────────────────────────────────────────────┘
```

### Key Formulas

#### Income Statement Drivers
```
Revenue = Prior Year × (1 + Growth Rate)
COGS = Revenue × (1 - Gross Margin %)
Gross Profit = Revenue - COGS
SG&A = Revenue × SG&A %
EBITDA = Gross Profit - SG&A
D&A = Prior PP&E × D&A Rate OR Revenue × D&A %
EBIT = EBITDA - D&A
Interest = Avg Debt × Interest Rate
EBT = EBIT - Interest
Taxes = EBT × Tax Rate
Net Income = EBT - Taxes
```

#### Balance Sheet Drivers
```
Accounts Receivable = Revenue × (DSO / 365)
Inventory = COGS × (DIO / 365)
Accounts Payable = COGS × (DPO / 365)
PP&E = Prior PP&E + Capex - D&A
Retained Earnings = Prior RE + Net Income - Dividends
Cash = Total Liabilities + Equity - Other Assets (plug)
```

#### Cash Flow Statement
```
Operating Cash Flow:
  Net Income
  + D&A (non-cash)
  - Increase in AR
  - Increase in Inventory
  + Increase in AP
  = Cash from Operations

Investing Cash Flow:
  - Capex
  = Cash from Investing

Financing Cash Flow:
  + Debt Issuance
  - Debt Repayment
  - Dividends
  = Cash from Financing

Net Change in Cash = CFO + CFI + CFF
```

---

## Output Format

```markdown
# Financial Model: [Company Name]

**Projection Period**: [Years]
**Base Year**: [Year]
**Currency**: [USD/CNY/etc.]

---

## Key Assumptions

| Driver | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
|--------|--------|--------|--------|--------|--------|
| Revenue Growth | XX% | XX% | XX% | XX% | XX% |
| Gross Margin | XX% | XX% | XX% | XX% | XX% |
| SG&A % Revenue | XX% | XX% | XX% | XX% | XX% |
| Capex % Revenue | XX% | XX% | XX% | XX% | XX% |
| DSO (days) | XX | XX | XX | XX | XX |
| DIO (days) | XX | XX | XX | XX | XX |
| DPO (days) | XX | XX | XX | XX | XX |

---

## Income Statement Projection

| ($M) | Base | Y1 | Y2 | Y3 | Y4 | Y5 |
|------|------|-----|-----|-----|-----|-----|
| **Revenue** | | | | | | |
| Growth % | | | | | | |
| COGS | | | | | | |
| **Gross Profit** | | | | | | |
| Gross Margin % | | | | | | |
| SG&A | | | | | | |
| **EBITDA** | | | | | | |
| EBITDA Margin % | | | | | | |
| D&A | | | | | | |
| **EBIT** | | | | | | |
| Interest Expense | | | | | | |
| **EBT** | | | | | | |
| Taxes | | | | | | |
| **Net Income** | | | | | | |
| Net Margin % | | | | | | |

---

## Balance Sheet Projection

| ($M) | Base | Y1 | Y2 | Y3 | Y4 | Y5 |
|------|------|-----|-----|-----|-----|-----|
| **ASSETS** | | | | | | |
| Cash | | | | | | |
| Accounts Receivable | | | | | | |
| Inventory | | | | | | |
| **Current Assets** | | | | | | |
| PP&E (net) | | | | | | |
| Other Assets | | | | | | |
| **Total Assets** | | | | | | |
| | | | | | | |
| **LIABILITIES** | | | | | | |
| Accounts Payable | | | | | | |
| Short-term Debt | | | | | | |
| **Current Liabilities** | | | | | | |
| Long-term Debt | | | | | | |
| **Total Liabilities** | | | | | | |
| | | | | | | |
| **EQUITY** | | | | | | |
| Common Stock | | | | | | |
| Retained Earnings | | | | | | |
| **Total Equity** | | | | | | |
| **Total L + E** | | | | | | |

✓ Balance Check: Assets = Liabilities + Equity

---

## Cash Flow Statement

| ($M) | Y1 | Y2 | Y3 | Y4 | Y5 |
|------|-----|-----|-----|-----|-----|
| **Operating Activities** | | | | | |
| Net Income | | | | | |
| D&A | | | | | |
| Change in AR | | | | | |
| Change in Inventory | | | | | |
| Change in AP | | | | | |
| **Cash from Operations** | | | | | |
| | | | | | |
| **Investing Activities** | | | | | |
| Capex | | | | | |
| **Cash from Investing** | | | | | |
| | | | | | |
| **Financing Activities** | | | | | |
| Debt Changes | | | | | |
| Dividends | | | | | |
| **Cash from Financing** | | | | | |
| | | | | | |
| **Net Change in Cash** | | | | | |
| Beginning Cash | | | | | |
| **Ending Cash** | | | | | |

---

## Key Metrics Summary

| Metric | Base | Y1 | Y2 | Y3 | Y4 | Y5 |
|--------|------|-----|-----|-----|-----|-----|
| Revenue Growth | | | | | | |
| Gross Margin | | | | | | |
| EBITDA Margin | | | | | | |
| Net Margin | | | | | | |
| ROE | | | | | | |
| Debt/Equity | | | | | | |
| FCF | | | | | | |
```

---

## Tips for Better Results

1. **Provide clean historical data** in a consistent format
2. **Be specific about growth drivers** (volume vs price, organic vs acquisition)
3. **Specify industry context** for appropriate benchmarks
4. **Ask for scenario analysis** to understand range of outcomes
5. **Request sensitivity tables** for key assumptions

---

## Limitations

- Projections are only as good as the assumptions
- Cannot model complex corporate structures
- Does not account for one-time items automatically
- Simplified tax calculations
- Currency assumed constant (no FX modeling)

---

*Built by the Claude Office Skills community. Contributions welcome!*
