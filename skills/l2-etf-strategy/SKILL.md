---
name: l2-etf-strategy
description: "Operate and reproduce the user's L2 ETF strategy package. Use when the user asks about L2 ETF, TRD_K20_ADV50M_NoKCB, quarterly ETF rebalancing, ETF picks/trades, live ETF holdings, NAV logs, or reproducing the ETF backtest/experiment evidence from the 2026-06-10 package."
---

# L2 ETF Strategy

## Orientation

Use this skill for the user's locked L2 ETF strategy line only. Do not mix it with Turtle stock rules, VCP experiments, or single-stock live trading logic.

Core asset root:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/l2-etf-strategy"
PKG="$SKILL_DIR/assets/L2_ETF_STRATEGY_EXPERIMENT_PACKAGE_2026-06-10"
LIVE="$PKG/01_live_strategy/L2_ETF_LIVE"
BACKTEST="$PKG/02_backtest_reproduction/L2_ETF_BACKTEST"
SOURCE_DATA="$PKG/03_source_data/L2_ETF_DATA_2026-05-29"
```

Always start by reading `references/handoff.md`. For live rebalancing or holdings work, also read `references/live-strategy.md` and `references/live-changelog.md`. For performance reproduction, read `references/backtest-reproduction.md`.

## Locked Strategy

- Strategy: `TRD_K20_ADV50M_NoKCB`.
- Capital segment: 50,000 RMB.
- Pool: cleaned A-share equity ETF/LOF universe.
- Live exclusion: ETF codes prefixed `588` or `589`.
- Liquidity filter: 60-day average traded value >= 50,000,000 RMB.
- Signal: 120-day momentum Top 20.
- Weighting: 20 equal-weight ETF positions, 100-share lots, floor sizing.
- Rebalance: quarterly.
- No stop loss, no take profit, no news-driven mid-quarter trading.
- Regime, REV, and ADAPT are not enabled for live operation.

The package cache is historical: source data is dated 2026-05-29. If a user asks for latest/current/future rebalance output, refresh or obtain up-to-date ETF pool and kline cache first, then run the same workflow with `L2_ETF_DATA_ROOT` pointing at the refreshed data. Do not present stale 2026-05-29 output as a current signal.

## Live Rebalance Workflow

Use this when generating quarterly `picks_YYYY-MM-DD.csv` and `trades_YYYY-MM-DD.csv`.

1. Inspect `current_holdings.json` in `LIVE` and note confirmed live state. As of the package handoff, 2026-06-10 status is `initial_build_completed_20_etfs`; `159381` is intentionally above original equal-weight target and should be corrected only at the next quarterly rebalance unless the user explicitly requests interim action.
2. Confirm data freshness. For bundled historical reproduction, use `SOURCE_DATA`. For any current rebalance, use refreshed data with the same layout: `all_etf_pool.csv` plus `kline_cache_all/*.json`.
3. Run from the live directory:

```bash
cd "$LIVE"
L2_ETF_DATA_ROOT="$SOURCE_DATA" python3 quarterly_picks.py --cutoff YYYY-MM-DD --capital 50000
```

If the cutoff should be the newest common date in the cache, omit `--cutoff`. Use `--show-pool-size` for a quick eligibility check. Do not use `--commit` unless the user confirms actual fills or explicitly asks to update holdings.

Generated files are written beside `quarterly_picks.py`. When preserving canonical assets matters, copy `LIVE` to a temporary working directory first and run there with `L2_ETF_LIVE_HOME` set to that copy.

## Backtest Reproduction Workflow

Use this to verify the locked performance evidence:

```bash
cd "$BACKTEST"
python3 run_capital_sweep.py
diff ./baselines_capsweep/capsweep_summary.csv ./capsweep_summary.csv
```

Expected headline in stdout:

```text
TRD_K20_ADV50M  ret: 1w:+110.5%  2w:+117.8%  3w:+119.0%  5w:+120.8%  10w:+122.6%  20w:+123.3%
```

No `diff` output means the regenerated `capsweep_summary.csv` matches the reference. The 50,000 RMB line corresponds to about +120.83% total return, -20.62% max drawdown, and 5.86 Calmar for 2024-01 to 2026-05.

The scripts require `pandas` and `numpy`. If the default `python3` lacks them, use a Python environment that has both installed.

## Reporting Rules

- State the cutoff date, data root, eligible pool size, and whether the run used bundled or refreshed data.
- Separate target picks, trade diffs, and confirmed holdings.
- Mention that orders are operational outputs from the user's predefined strategy, not broker execution.
- If data is stale, say so plainly and avoid implying the list is current.
- Preserve evidence boundaries: the package supports the ETF strategy line only and excludes Turtle stock and later VCP experiments.
