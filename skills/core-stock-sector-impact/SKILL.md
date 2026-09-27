---
name: core-stock-sector-impact
description: Analyze whether a caller-provided set of core stocks is leading, confirming, or exhausting risk in a sector/index/ETF by classifying each core stock into short-window up/sideways/down states, measuring breadth diffusion, and backtesting target forward returns, downside amplitude, and drawdowns. Use when the user asks to see whether core leaders affect or warn about a板块/指数/ETF, asks for 核心标的影响板块, 龙头扩散, 横盘/下跌数量, 板块风险温度计, or wants a reusable Tushare-based analysis where the core stock basket is supplied at call time.
---

# Core Stock Sector Impact

Use this skill to turn a qualitative question like “这些核心标的横盘/下跌会不会影响板块？” into a reproducible breadth analysis.

The skill's default idea:

```text
core stocks -> short-window state classification -> breadth regime
-> target forward return, downside amplitude, and drawdown distribution
```

## Required Inputs

Obtain or infer these before running analysis:

- **Target observation instrument**: sector/index/ETF/stock used as the板块代理, e.g. `930713.CSI`, `515070.SH`, `399006.SZ`.
- **Core stock basket**: caller-provided list of core stocks in `ts_code:name` form, e.g. `300308.SZ:中际旭创,300502.SZ:新易盛`.
- **Window and thresholds**: default `5` trading days and `±5%`.
- **Analysis interval**: default from `20250101`; choose earlier when the user wants more samples.

Use Tushare for historical prices. Check `TUSHARE_TOKEN` before running. If the target is a CSI-style index (`*.CSI`), use `index_daily`; if it is an ETF (`515070.SH`, `159819.SZ`, etc.), use `fund_daily`; if it is a stock, use qfq stock prices.

## Core State Definitions

Default classification for each core stock:

| State | Rule |
| --- | --- |
| 上行 | `state_window` return `> +band` |
| 横盘 | `state_window` return between `-band` and `+band` |
| 下跌 | `state_window` return `< -band` |

Default values: `state_window=5`, `band=0.05`.

Use the user's domain judgment to adjust these. For high-volatility tech themes, `±5%` over 5 days is often a better横盘 band than `0%`.

## Breadth Regimes

For an `N` stock basket, default majority threshold is `floor(N/2)+1`.

| Regime | Rule | Interpretation |
| --- | --- | --- |
| 增长扩散 | up count >= majority | 主线仍有进攻性 |
| 横盘钝化 | sideways count >= majority | 动能钝化；重点看后续跌幅/回撤幅度 |
| 下降扩散 | down count >= majority | 风险已显性释放；未必适合继续线性看空 |
| 混合 | none of the above | 分歧状态，单独看结构 |

Do not stop at “下跌概率”. Always report amplitude:

- forward average return across all valid samples
- P10 forward return
- worst forward return
- average forward return conditional on negative forward-return samples only
- P10 forward max drawdown
- worst forward max drawdown

This distinction matters: 横盘扩散 may have lower immediate跌概率 but larger tail loss; 下降扩散 often means the first leg of risk has already happened.

When presenting mixed full-sample and conditional metrics, label the denominator explicitly. Do not write ambiguous phrases like `平均亏损` by itself. Use wording such as `全样本平均收益` for unconditional means and `亏损样本平均收益` / `仅负收益样本均值` for conditional loss means.

## Baseline, Significance, And Stability

Do not treat a regime's raw mean as evidence that the core basket causes target performance. The script must report three layers:

1. **基准比较**：全样本无条件基准；对每个 regime 使用剔除该 regime 的 leave-one-regime-out 基准；再给出目标自身过去 `state_window` 收益正/非正的趋势基准。任何比较都要写清楚分母。
2. **显著性**：每个 regime、每个 horizon 至少报告样本数、状态均值、基准均值、增量、bootstrap 95% CI、双侧 permutation p 值和正收益比例差异；同时检查最大回撤差异。统计显著不等于经济显著。
3. **稳定性**：按前半/后半样本和自然年度重复比较，保留每个子样本 regime 数量、增量方向、显著性和最差/最佳阶段。若方向跨阶段反转、样本集中在单一年份或对照为空，应降级为阶段性现象。

主比较优先使用 leave-one-regime-out，避免把当前 regime 包含在全样本基准中造成机械稀释。置换检验和 bootstrap 仅用于描述当前样本不确定性，不能替代样本审计、交易日对齐和经济机制。

## Script

Use the bundled script for deterministic analysis:

```bash
python3 ~/.codex/skills/core-stock-sector-impact/scripts/core_impact_breadth.py \
  --target-code 930713.CSI \
  --target-name 中证人工智能主题指数 \
  --stocks "300308.SZ:中际旭创,300502.SZ:新易盛,300394.SZ:天孚通信,600183.SH:生益科技,002463.SZ:沪电股份,300476.SZ:胜宏科技,601138.SH:工业富联" \
  --analysis-start 20250101 \
  --fetch-start 20240101 \
  --end-date today \
  --state-window 5 \
  --band 0.05 \
  --horizons 5,10,20 \
  --output-dir outputs/core_stock_sector_impact_ai
```

Key options:

- `--stocks`: comma-separated `code:name` items supplied by the user.
- `--stocks-file`: CSV with `code`/`name` columns when the basket is long.
- `--target-code`: index, ETF, or stock to evaluate.
- `--target-type`: `auto`, `index`, `fund`, or `stock`; leave `auto` unless inference fails.
- `--end-date`: defaults to `today` and is resolved at runtime. Use `today`/`now`/`auto` for current-day monitoring, or pass `YYYYMMDD` for a frozen historical run. When the resolved end date is today, the script refreshes same-day cache automatically to avoid reusing stale intraday/pre-close files.
- `--state-window`: classification window; default `5`.
- `--band`: up/sideways/down threshold; default `0.05`.
- `--majority-count`: override breadth threshold if the user wants e.g. `>=4` on a 7-stock basket.

Outputs:

- `core_stock_sector_impact_report.md`
- `daily_panel.csv`
- `stock_state_detail.csv`
- `summary_target_by_regime.csv`
- `summary_core_basket_by_regime.csv`
- `baseline_summary.csv`：全样本、leave-one-regime-out、目标过去趋势基准
- `regime_significance.csv`：收益、最大回撤和正收益率的增量、bootstrap CI、置换 p 值
- `regime_stability.csv`：前后半样本/年度稳定性、方向一致性和阶段显著性
- count-level summaries by `up_count`, `sideways_count`, and `down_count`

## Interpretation Template

Answer in this order:

1. State the current breadth: `增长/横盘/下降数量` and regime.
2. Say whether this is a fresh warning, a钝化 signal, or already-risk-released state.
3. Compare forward 5/10 day target behavior by regime.
4. Include amplitude, not just probability: P10, worst, conditional negative-return average, and drawdown tail. State whether each average is full-sample or conditional.
5. Mention sample-size caveats for extreme states like all横盘 or all下跌.
6. Compare against the explicit baseline, report p-value/CI only with sample counts, and say whether the sign survives the half-sample/year stability check.
7. Give a monitoring rule in plain language.

Example conclusion shape:

```text
横盘扩散不是“马上一定跌”，但它表示核心锚停止主动进攻。
在历史样本里，横盘扩散后的全样本均值未必最差，但 P10 / worst / 亏损样本平均收益更差，
所以它是性价比下降和尾部风险放大的信号。

下降扩散说明风险已经显性释放，短线仍弱，但不宜把它机械当作新增追空信号。
```

## Guardrails

- Do not call the target a “fund” if the analysis used an index. Clearly distinguish index proxy from ETF tracking products.
- Do not infer constituent holdings unless you actually queried index constituents or fund holdings.
- Do not use future returns in signal construction; use future returns only for evaluation.
- Do not rely only on hit probability. Always inspect magnitude and drawdown.
- Do not mix full-sample averages and conditional-loss averages without naming the sample base. If a table uses both, explain the denominator before interpreting the numbers.
- Do not call a regime predictive from a raw mean alone; require a stated baseline, uncertainty interval/p-value, and stability check.
- Do not interpret a significant result with a tiny or concentrated sample as a robust effect; explicitly downgrade it.
- If the sample is small, state it directly and avoid hard trading rules.
