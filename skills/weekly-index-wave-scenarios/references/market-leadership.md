# Market-leadership protocol

## What counts as a total leader

Use a reviewed basket, not a single “king stock”. Include 3–5 names in each role:

| Role | Selection rule | Why it matters |
|---|---|---|
| `market_anchor` | large market-cap and high-liquidity stock with persistent index influence | tests broad-index carrying power |
| `style_leader` | strongest representative of the currently leading style | tests whether the market's preferred risk exposure is intact |
| `narrative_leader` | stock at the centre of the active policy/technology/industry narrative | tests speculative risk appetite |

Review roles monthly and whenever a new industry theme replaces the old one. Market capitalisation alone is insufficient; use turnover/liquidity, relative strength, sector influence, and whether the stock is actually leading the current market narrative. Retain the previous roster in the report metadata so historical testing is reproducible.

## Weekly interpretation

For every leader calculate: weekly close, 4-week return, EMA13, EMA34, last confirmed pivot high/low, and its relative performance against the selected index.

- **Broad confirmation:** at least 60% of the basket is above both EMA13 and EMA34, with key leaders above prior pivots.
- **Broad deterioration:** at least 60% is below both averages, with key leaders below prior lows.
- **Divergence:** neither threshold holds, or market anchors and narrative leaders disagree.

The signal alters confidence by at most one band. It cannot override a price-based index invalidation.
