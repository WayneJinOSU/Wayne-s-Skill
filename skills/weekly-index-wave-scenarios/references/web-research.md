# Official web-research workflow

Use web research when a news API is absent or lacks permission. Search engines and media are discovery tools only. An event becomes score-eligible only after opening an original source and recording its publication time and URL.

## Source order

| Topic | Primary sources | What to capture |
|---|---|---|
| Monetary policy and liquidity | [PBOC](https://www.pbc.gov.cn/), ChinaMoney | policy wording, policy operation, LPR/RRR/OMO details, timestamp |
| Capital-market rules and market stability | [CSRC](https://www.csrc.gov.cn/), [State Council](https://www.gov.cn/) | actual rule or policy text, implementation date, scope |
| A-share IPO and refinancing | [SSE](https://www.sse.com.cn/), [SZSE](https://www.szse.cn/), [BSE](https://www.bse.cn/), issuer disclosure | board, status, proceeds/offer size, timetable, prospectus or disclosure URL |
| Macro releases | [NBS](https://www.stats.gov.cn/), PBOC | release value, consensus/surprise if independently available, release time |
| Listed-company systemic events | company IR page and exchange disclosure | issuer announcement, exact status, affected listed comparables |
| Offshore shock | original central-bank, statistical agency, exchange, or government page | original decision/release and China transmission channel |

## Research sequence

1. Start with one focused query for the current review period and the event class.
2. Identify the strongest candidate and open the original page; do not collect a large unfiltered news list.
3. Extract only the factual fields required by `event-ledger-template.csv`.
4. State whether it changes policy, liquidity, earnings, valuation, or only confirms an existing expectation.
5. If the surprise or transmission is unclear, record `direction=0` and explain why. Do not force a bullish/bearish label.

## IPO-specific checks

For an issuer such as 智谱 or 长鑫, confirm the actual lifecycle from a regulator, exchange, or issuer filing before it enters the event ledger. Capture board, filing/acceptance/registration/pricing/listing status, public proceeds/offer size, timing, comparable listed companies, and source URL. A company name in media discussion alone remains a watchlist item.
