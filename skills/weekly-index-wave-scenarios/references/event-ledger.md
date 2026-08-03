# Event ledger rules

## Evidence hierarchy

| Level | Sources | Permitted use |
|---|---|---|
| 1 | State Council, PBOC, CSRC, exchange, company filing | Confirmed event; can affect confidence |
| 2 | Named primary reporting or official interview | Provisional observation; modest confidence effect |
| 3 | Unattributed media, social media, market rumour | Watchlist only; no scenario-score effect |

Every item needs a source URL or document identifier, the first market-available timestamp (`published_at`), and an effective window. When facts later change, append a new record instead of overwriting the original item.

## IPO event protocol

Record issuer, exchange/board, sector, lifecycle status, disclosed expected proceeds, pricing/offer size if available, expected or actual listing date, comparable listed companies, and source evidence.

Evaluate four independent channels:

1. **Capital supply:** subscription, issuance and concurrent refinancing may divert marginal funds.
2. **Valuation anchor:** the issuer may re-rate comparable listed firms upward or downward.
3. **Industry expectations:** a strategic issuer can validate or challenge a sector investment thesis.
4. **Risk appetite:** a highly watched listing can alter demand for growth assets beyond its sector.

Do not set `direction=-1` merely because an IPO is large. Set `direction=0` where channels conflict and explain the ambiguity in the report.

## Event score

`event_score = direction × confidence × status_weight × source_weight`

- `direction`: -1, 0, or 1.
- `confidence`: 0 to 1, based on evidence and market relevance.
- `status_weight`: rumour 0; filing/accepted 0.25; registered 0.5; priced 0.8; listed/post_listing 1.
- `source_weight`: official 1; reputable media 0.5; unverified 0.

The 30-day weighted total is shown as context only. It adjusts a scenario confidence band by at most one level and never changes a price zone or invalidation level.
